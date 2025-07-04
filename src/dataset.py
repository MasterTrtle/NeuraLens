from datasets import Dataset as HFDataset, DatasetDict
from torch.utils.data import DataLoader
from PIL import Image
from torchvision import transforms
import numpy as np
from pathlib import Path
import torch
from sklearn.model_selection import train_test_split
from typing import Any


# TODO add multiprocessing to speed up image loading
class tissue_dataset:
    def __init__(
        self,
        images_dir_path="src/dataset/Motic-Human-tissues",
        transform=None,
        split_ratio=0.8,
        train_batch_size=8,
        val_batch_size=8,
    ):
        """Initializes the tissue dataset.
        Args:
            images_dir_path (str): Path to the directory containing tissue images.
            transform (callable, optional): A function/transform that takes in an image and returns a transformed version.
            split_ratio (float): The ratio of the dataset to be used for training.
            train_batch_size (int): The number of samples per batch for training.
            val_batch_size (int): The number of samples per batch for validation.
        """
        self.split_ratio = split_ratio
        self.train_batch_size = train_batch_size
        self.val_batch_size = val_batch_size

        images = []
        focus = []
        type_labels = []
        zoom = []

        images_dir = Path(images_dir_path)
        for image in images_dir.glob("*.jpg"):
            image_name = image.name.lower()
            if image_name.find("calibration") == -1:
                images.append(str(image))

                if image_name.find("focus") != -1:
                    focus.append(0)
                else:
                    focus.append(1)

                position = image_name.find("4x")
                if position != -1:
                    zoom.append(4)
                else:
                    position = image_name.find("10x")
                    if position != -1:
                        zoom.append(10)
                    else:
                        position = image_name.find("10x")
                        if position != -1:
                            zoom.append(10)
                        else:
                            position = image_name.find("20x")
                            if position != -1:
                                zoom.append(20)
                            else:
                                position = image_name.find("40x")
                                if position != -1:
                                    zoom.append(40)

                type_labels.append(image_name[: position - 1].split("-")[0])
        print(f"Found {len(images)} images in {images_dir_path}")

        if transform is not None:
            self.transform = transform
        else:
            self.transform = transforms.ToTensor()

        self.zoom_classes = sorted(list(set(zoom)))  # e.g., [4, 10, 20, 40]
        self.type_classes = sorted(
            list(set(type_labels))
        )  # e.g., ['adipose', 'blood', 'bone', etc.]
        self.focus_classes = [0, 1]  # Focused (0) or Unfocused (1)

        # Create mappings
        self.zoom_to_idx = {
            zoom_val: idx for idx, zoom_val in enumerate(self.zoom_classes)
        }
        self.type_to_idx = {
            type_name: idx for idx, type_name in enumerate(self.type_classes)
        }

        # Convert zoom and type to indices
        zoom_indices = [self.zoom_to_idx[z] for z in zoom]
        type_indices = [self.type_to_idx[t] for t in type_labels]

        # Split data before creating HuggingFace datasets
        self._split_data(images, focus, zoom_indices, type_indices)

        type_classes_mapping = {v: k for k, v in self.type_to_idx.items()}
        zoom_classes_mapping = {v: k for k, v in self.zoom_to_idx.items()}
        focus_classes_mapping = {0: "focused", 1: "unfocused"}

        self.type_options = "\n".join(
            [f"{i}: {type_classes_mapping[i]}" for i in type_classes_mapping]
        )
        self.zoom_options = "\n".join(
            [f"{i}: {zoom_classes_mapping[i]}x" for i in zoom_classes_mapping]
        )
        self.focus_options = "\n".join(
            [f"{i}: {focus_classes_mapping[i]}" for i in focus_classes_mapping]
        )

        self.PROMPT = f"""Analyze this histopathology image and provide the following information:

        Tissue Type:
        {self.type_options}

        Zoom Level:
        {self.zoom_options}

        Focus Quality:
        {self.focus_options}

        Please respond in the following JSON format:
        {{
        "tissue_type": "X: tissue_name",
        "zoom_level": "Y: Zx",
        "focus_quality": "Z: focus_status"
        }}"""
        # Create HuggingFace DatasetDict
        self._create_hf_datasets()

    def _split_data(self, images, focus, zoom_indices, type_indices):
        """Split the data into train and validation sets."""
        # Split the indices without stratification
        train_indices, val_indices = train_test_split(
            range(len(images)), test_size=1.0 - self.split_ratio, random_state=42
        )

        # Create train split
        self.train_data = {
            "image_path": [images[i] for i in train_indices],
            "focus": [focus[i] for i in train_indices],
            "zoom": [zoom_indices[i] for i in train_indices],
            "type": [type_indices[i] for i in train_indices],
        }

        # Create validation split
        self.val_data = {
            "image_path": [images[i] for i in val_indices],
            "focus": [focus[i] for i in val_indices],
            "zoom": [zoom_indices[i] for i in val_indices],
            "type": [type_indices[i] for i in val_indices],
        }

    def _create_hf_datasets(self):
        """Create HuggingFace DatasetDict with train and validation splits."""
        # Create individual datasets
        print("Creating HuggingFace datasets...")
        train_dataset = HFDataset.from_dict(self.train_data)
        val_dataset = HFDataset.from_dict(self.val_data)

        # Apply message formatting for chat-based training
        print("Formatting training data...")
        train_dataset = train_dataset.map(self._format_data, batched=False)

        print("Formatting validation data...")
        val_dataset = val_dataset.map(self._format_test_data, batched=False)

        # Create DatasetDict
        self.dataset = DatasetDict({"train": train_dataset, "validation": val_dataset})

    def build_train_val_loaders(self) -> None:
        """Create DataLoaders for training and validation."""
        self.train_dataset = self.dataset["train"]
        self.val_dataset = self.dataset["validation"]

        # Set format for PyTorch compatibility
        self.train_dataset.set_format("torch")
        self.val_dataset.set_format("torch")

        # Create DataLoaders
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.train_batch_size,
            shuffle=True,
            collate_fn=self._collate_fn,
        )
        self.val_loader = DataLoader(
            self.val_dataset,
            batch_size=self.val_batch_size,
            collate_fn=self._collate_fn,
        )

    def _collate_fn(self, examples: list[dict[str, Any]]):
        texts = []
        images = []
        for example in examples:
            image = Image.open(example["image_path"]).convert("RGB")
            images.append(image)
            # print(f"Image: {example['image_path']}, size: {image.size}")
            text = self.processor.apply_chat_template(
                example["messages"], add_generation_prompt=False, tokenize=False
            ).strip()
            # print(f"Text: {text}, length: {len(text)}")
            texts.append(text)

        # print(f"Number of images: {len(images)}, Number of texts: {len(texts)}")

        # Process each image-text pair individually and then batch them
        batched_inputs = []
        for i in range(len(images)):
            # Process one image-text pair at a time
            single_batch = self.processor(
                text=[texts[i]], images=[images[i]], return_tensors="pt", padding=True
            )
            batched_inputs.append(single_batch)

        # Now manually batch the results
        batch = {}
        for key in batched_inputs[0].keys():
            if key == "pixel_values":
                # Stack image tensors
                batch[key] = torch.cat([b[key] for b in batched_inputs], dim=0)
            else:
                # Pad and stack text tensors
                max_length = max(b[key].shape[1] for b in batched_inputs)
                padded_tensors = []
                for b in batched_inputs:
                    tensor = b[key]
                    if tensor.shape[1] < max_length:
                        # Pad with tokenizer's pad_token_id
                        padding = torch.full(
                            (tensor.shape[0], max_length - tensor.shape[1]),
                            self.processor.tokenizer.pad_token_id,
                            dtype=tensor.dtype,
                        )
                        tensor = torch.cat([tensor, padding], dim=1)
                    padded_tensors.append(tensor)
                batch[key] = torch.cat(padded_tensors, dim=0)

        # The labels are the input_ids, with the padding and image tokens masked in
        # the loss computation
        labels = batch["input_ids"].clone()

        # Mask image tokens
        image_token_id = self.processor.tokenizer.convert_tokens_to_ids(
            self.processor.tokenizer.special_tokens_map["boi_token"]
        )

        # Mask tokens that are not used in the loss computation
        labels[labels == self.processor.tokenizer.pad_token_id] = -100
        labels[labels == image_token_id] = -100
        labels[labels == 262144] = -100

        batch["labels"] = labels
        return batch

    def set_processor(self, processor):
        """Set the processor for the collate function."""
        self.processor = processor

    def _format_data(self, example: dict[str, Any]) -> dict[str, Any]:
        """Format data for chat-based training."""
        tissue_type_idx = example["type"]
        tissue_type_name = self.type_classes[tissue_type_idx]
        zoom_idx = example["zoom"]
        zoom_value = self.zoom_classes[zoom_idx]
        focus_idx = example["focus"]
        focus_status = "focused" if focus_idx == 0 else "unfocused"

        # Randomly choose between JSON and natural language responses (70% JSON, 30% natural)
        import random

        use_json = random.random() < 0.7

        if use_json:
            response_text = f"""{{
    "tissue_type": "{tissue_type_idx}: {tissue_type_name}",
    "zoom_level": "{zoom_idx}: {zoom_value}x",
    "focus_quality": "{focus_idx}: {focus_status}"
    }}"""
        else:
            response_text = f"This histopathology image shows {tissue_type_name} tissue at {zoom_value}x magnification. The image appears to be {focus_status}."

        example["messages"] = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": self.PROMPT},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": response_text},
                ],
            },
        ]
        return example

    def _format_test_data(self, example: dict[str, Any]) -> dict[str, Any]:
        """Format data for chat-based training."""
        example["messages"] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                    },
                    {
                        "type": "text",
                        "text": self.PROMPT,
                    },
                ],
            },
        ]
        return example

    def postprocess(
        self, prediction: list[dict[str, str]], do_full_match: bool = False
    ) -> dict:
        response_text = prediction[0]["generated_text"]

        # Clean the response text first
        response_text = response_text.strip()

        # Try to extract the first JSON block
        import re
        import json

        # Look for JSON pattern
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        json_matches = re.findall(json_pattern, response_text)

        for json_match in json_matches:
            try:
                parsed = json.loads(json_match)
                if all(
                    key in parsed
                    for key in ["tissue_type", "zoom_level", "focus_quality"]
                ):
                    return {
                        "tissue_type": self._extract_index(
                            parsed.get("tissue_type", "")
                        ),
                        "zoom_level": self._extract_index(parsed.get("zoom_level", "")),
                        "focus_quality": self._extract_index(
                            parsed.get("focus_quality", "")
                        ),
                    }
            except (json.JSONDecodeError, KeyError):
                continue

        # Fallback to text parsing if no valid JSON found
        return {
            "tissue_type": self._extract_tissue_from_text(response_text),
            "zoom_level": self._extract_zoom_from_text(response_text),
            "focus_quality": self._extract_focus_from_text(response_text),
        }

    def _extract_index(self, text: str) -> int:
        """Extract index from 'X: value' format"""
        try:
            return int(text.split(":")[0].strip())
        except (ValueError, IndexError):
            return -1

    def __len__(self):
        return len(self.dataset["train"]) + len(self.dataset["validation"])

    def get_num_classes(self):
        """Returns the number of classes for each label type."""
        return {
            "focus": 2,  # focused (0) or unfocused (1)
            "zoom": len(self.zoom_classes),
            "type": len(self.type_classes),
        }

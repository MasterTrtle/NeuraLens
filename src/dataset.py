from datasets import Dataset as HFDataset, DatasetDict
from torch.utils.data import DataLoader
from PIL import Image
from torchvision import transforms
import numpy as np
from pathlib import Path
import torch
from sklearn.model_selection import train_test_split
from typing import Any

#TODO add multiprocessing to speed up image loading
class tissue_dataset:
    def __init__(self, images_dir_path="src/dataset/Motic-Human-tissues", transform=None, split_ratio=0.8, batch_size=8):
        """ Initializes the tissue dataset.
        Args:
            images_dir_path (str): Path to the directory containing tissue images.
            transform (callable, optional): A function/transform that takes in an image and returns a transformed version.
            split_ratio (float): The ratio of the dataset to be used for training.
            batch_size (int): The number of samples per batch.
        """
        self.split_ratio = split_ratio
        self.batch_size = batch_size

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
        self.type_classes = sorted(list(set(type_labels)))  # e.g., ['adipose', 'blood', 'bone', etc.]
        self.focus_classes = [0, 1]  # Focused (0) or Unfocused (1)
        
        # Create mappings
        self.zoom_to_idx = {zoom_val: idx for idx, zoom_val in enumerate(self.zoom_classes)}
        self.type_to_idx = {type_name: idx for idx, type_name in enumerate(self.type_classes)}

        # Convert zoom and type to indices
        zoom_indices = [self.zoom_to_idx[z] for z in zoom]
        type_indices = [self.type_to_idx[t] for t in type_labels]
    
        # Split data before creating HuggingFace datasets
        self._split_data(images, focus, zoom_indices, type_indices)
        


        type_classes_mapping = {v: k for k, v in self.type_to_idx.items()}
        self.options = "\n".join(
            [f"{i}: {type_classes_mapping[i]}" for i in type_classes_mapping]
        )
        self.PROMPT = f"What is the most likely body part type shown in the histopathology image?\n{self.options}"
        
        # Create HuggingFace DatasetDict
        self._create_hf_datasets()

    def _split_data(self, images, focus, zoom_indices, type_indices):
        """Split the data into train and validation sets."""
        # Split the indices without stratification
        train_indices, val_indices = train_test_split(
            range(len(images)), 
            test_size=1.0 - self.split_ratio,
            random_state=42
        )
        
        # Create train split
        self.train_data = {
            "image_path": [images[i] for i in train_indices],
            "focus": [focus[i] for i in train_indices],
            "zoom": [zoom_indices[i] for i in train_indices],
            "type": [type_indices[i] for i in train_indices]
        }
        
        # Create validation split
        self.val_data = {
            "image_path": [images[i] for i in val_indices],
            "focus": [focus[i] for i in val_indices],
            "zoom": [zoom_indices[i] for i in val_indices],
            "type": [type_indices[i] for i in val_indices]
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
        val_dataset = val_dataset.map(self._format_data, batched=False)
        
        # Create DatasetDict
        self.dataset = DatasetDict({
            "train": train_dataset,
            "validation": val_dataset
        })


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
            batch_size=self.batch_size, 
            shuffle=True,
            collate_fn=self._collate_fn
        )
        self.val_loader = DataLoader(
            self.val_dataset, 
            batch_size=self.batch_size, 
            shuffle=False,
            collate_fn=self._collate_fn
        )



    def _collate_fn(self, examples: list[dict[str, Any]]):
        texts = []
        images = []
        for example in examples:
            image = Image.open(example["image_path"]).convert("RGB")
            images.append(image)
            texts.append(self.processor.apply_chat_template(
                example["messages"], add_generation_prompt=False, tokenize=False
            ).strip())

        # Tokenize the texts and process the images
        batch = self.processor(text=texts, images=images, return_tensors="pt", padding=True)

        # The labels are the input_ids, with the padding and image tokens masked in
        # the loss computation
        labels = batch["input_ids"].clone()

        # Mask image tokens
        image_token_id = [
            self.processor.tokenizer.convert_tokens_to_ids(
                self.processor.tokenizer.special_tokens_map["boi_token"]
            )
        ]
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
        # Get the tissue type label and convert to class name
        tissue_type_idx = example["type"]
        tissue_type_name = self.type_classes[tissue_type_idx]
        
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
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": f"{tissue_type_idx}: {tissue_type_name}",
                    },
                ],
            },
        ]
        return example

    def __len__(self):
        return len(self.dataset["train"]) + len(self.dataset["validation"])

    def get_num_classes(self):
        """Returns the number of classes for each label type."""
        return {
            'focus': 2,  # focused (0) or unfocused (1)
            'zoom': len(self.zoom_classes),
            'type': len(self.type_classes)
        }
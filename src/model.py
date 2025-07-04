import os
import dotenv
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
import torch
from peft import PeftModel

# Load environment variables from .env file
dotenv.load_dotenv(".env")
# Access the HF_TOKEN environment variable
HF_TOKEN = os.getenv("HF_TOKEN")


def load_base_model(model_id="google/medgemma-4b-it"):

    # Check if GPU supports bfloat16
    if torch.cuda.get_device_capability()[0] < 8:
        raise ValueError(
            "GPU does not support bfloat16, please use a GPU that supports bfloat16."
        )

    model_kwargs = dict(
        attn_implementation="eager",
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    model_kwargs["quantization_config"] = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=model_kwargs["torch_dtype"],
        bnb_4bit_quant_storage=model_kwargs["torch_dtype"],
    )

    base_model = AutoModelForImageTextToText.from_pretrained(model_id, **model_kwargs)
    return base_model


def load_processor(model_id="google/medgemma-4b-it"):
    """
    Load the processor for the model.
    """
    processor = AutoProcessor.from_pretrained(model_id)
    # Use right padding to avoid issues during training
    processor.tokenizer.padding_side = "right"
    return processor


def load_peft_model(base_model, peft_config):
    """
    Load the PEFT model with the given configuration.
    """
    from peft import get_peft_model

    # Apply LoRA configuration to the model
    model = get_peft_model(base_model, peft_config)
    return model


def load_model(model_id="google/medgemma-4b-it", peft_config=None):
    """
    Load the base model, processor, and optionally the PEFT model.
    """
    base_model = load_base_model(model_id)
    processor = load_processor(model_id)

    if peft_config is not None:
        model = load_peft_model(base_model, peft_config)
    else:
        model = base_model

    return model, processor


def load_peft_model_from_checkpoint(checkpoint_path, model_id="google/medgemma-4b-it"):
    """
    Load a PEFT model from a checkpoint.
    """
    base_model = load_base_model(model_id)
    model = PeftModel.from_pretrained(base_model, checkpoint_path)
    return model

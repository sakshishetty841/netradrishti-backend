import io
from PIL import Image
import torch
import torchvision.transforms as T

# Standard ImageNet normalization parameters for pretrained models
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def get_transforms(is_training: bool = False, image_size: int = 224):
    """
    Returns PyTorch torchvision transforms.
    Ensures identical base normalization and resizing for training, validation, testing, and FastAPI inference.
    """
    if is_training:
        return T.Compose([
            T.Resize((image_size, image_size)),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomRotation(degrees=15),
            T.ColorJitter(brightness=0.1, contrast=0.1),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
    else:
        return T.Compose([
            T.Resize((image_size, image_size)),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])

def preprocess_image_bytes(image_bytes: bytes, image_size: int = 224) -> torch.Tensor:
    """
    Preprocesses raw fundus image bytes into a normalized 4D float tensor (1, 3, H, W) for model inference.
    """
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    transform = get_transforms(is_training=False, image_size=image_size)
    tensor = transform(pil_img)
    return tensor.unsqueeze(0) # Add batch dimension -> (1, 3, 224, 224)

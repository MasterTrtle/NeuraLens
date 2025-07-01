from torch.utils.data import Dataset, DataLoader
from PIL import Image
import os
from torchvision import transforms
import numpy as np
from pathlib import Path

class tissue_dataset(Dataset):
  def __init__(self, images_dir_path, transform=None):
    super(tissue_dataset, self).__init__()

    self.images = []
    self.focus = []
    self.type = []
    self.zoom = []

    images_dir = Path(images_dir_path)
    for image in images_dir.glob("*.jpg"):
        image_name = image.name.lower()
        if image_name.find("calibration") == -1 :
            self.images.append(images_dir / image_name)

            if image_name.find("focus") != -1 :
                self.focus.append(0)
            else :
                self.focus.append(1)

            position = image_name.find("4x")
            if position != -1 :
                self.zoom.append(4)
            else:
                position = image_name.find("10x")
                if position != -1 :
                    self.zoom.append(10)
                else:
                    position = image_name.find("10x")
                    if position != -1:
                        self.zoom.append(10)
                    else:
                        position = image_name.find("20x")
                        if position != -1:
                            self.zoom.append(20)
                        else:
                            position = image_name.find("40x")
                            if position != -1:
                                self.zoom.append(40)

            self.type.append(image_name[:position-1].split("-")[0])

    if transform is not None:
        self.transform = transform
    else :
        self.transform = transforms.ToTensor()

  def __len__(self):
    return len(self.images)

  def __getitem__(self, idx):
    image = np.array(Image.open(self.images[idx]).convert("RGB"))
    focus = self.focus[idx]
    zoom = self.zoom[idx]
    type = self.type[idx]


    return self.transform(image), focus, zoom, type




if __name__ == '__main__':


    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((512, 512)),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    dataset = tissue_dataset("Motic-Human tissues", transform=transform)

    # test
    print(len(dataset.images), len(dataset.type), len(dataset.focus), len(dataset.zoom))
    print(dataset.__getitem__(0))
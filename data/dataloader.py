from torch.utils.data import DataLoader, random_split
import torch

def split_dataset(tissue_dataset):

    dataset = tissue_dataset("Motic-Human tissues")
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42))
    return train_dataset, val_dataset

def create_dataloader(tissue_dataset, batch_size):
    loader = DataLoader(tissue_dataset, batch_size=batch_size, shuffle=True)
    return loader


if __name__ == '__main__':
    from dataset import tissue_dataset
    train_dataset, val_dataset = split_dataset(tissue_dataset)
    train_loader = create_dataloader(train_dataset, 8)
    val_loader = create_dataloader(val_dataset, 8)

    print(next(iter(train_loader)))
    print(next(iter(val_loader)))
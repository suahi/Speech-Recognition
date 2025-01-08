

import torch
import torch.nn as nn
import torch.nn.functional as F


# 定义Squeeze-and-Excitation模块
class SEBlock(nn.Module):
    def __init__(self, channels, reduction=16):
        super(SEBlock, self).__init__()
        self.fc1 = nn.Linear(channels, channels // reduction, bias=False)
        self.fc2 = nn.Linear(channels // reduction, channels, bias=False)

    def forward(self, x):
        batch_size, channels, _, _ = x.size()
        # Squeeze操作
        squeeze = F.adaptive_avg_pool2d(x, (1, 1)).view(batch_size, channels)
        # Excitation操作
        excitation = F.relu(self.fc1(squeeze))
        excitation = torch.sigmoid(self.fc2(excitation)).view(batch_size, channels, 1, 1)
        return x * excitation


# CNN模型
class AudioCNN(nn.Module):
    def __init__(self, num_classes):
        super(AudioCNN, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.LeakyReLU(),
            nn.BatchNorm2d(64)
        )
        self.se1 = SEBlock(64)

        self.conv2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.LeakyReLU(),
            nn.BatchNorm2d(128),
            nn.MaxPool2d(kernel_size=2),
        )
        self.se2 = SEBlock(128)

        self.conv3 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.LeakyReLU(),
            nn.BatchNorm2d(256)

        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.LeakyReLU(),
            nn.BatchNorm2d(512),
            nn.MaxPool2d(kernel_size=2),

        )


        self.fc1 = nn.Sequential(
            nn.Linear(512 * 9 * 1, 256),
            nn.LeakyReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.LeakyReLU(),
            nn.Dropout(0.3)
        )
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.conv1(x)
        # x = self.se1(x)  # 添加SE模块
        x = self.conv2(x)
        # x = self.se2(x)  # 添加SE模块
        x = self.conv3(x)
        # x = self.se3(x)  # 添加SE模块
        x = self.conv4(x)
        x = x.view(x.size(0), -1)  # 展平
        x = self.fc1(x)
        x = self.fc2(x)
        return x



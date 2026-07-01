# 鲁班猫环境安装指南

## 1、镜像烧录-Ubuntu20.02

[3. 系统镜像烧录 — 快速使用手册—基于LubanCat-RK3588系列板卡 文档](https://doc.embedfire.com/linux/rk3588/quick_start/zh/latest/quick_start/flash_img/flash_img.html)

## 2、初始用户名

[2. 用户名及密码 — 快速使用手册—基于LubanCat-RK356x系列板卡 文档](https://doc.embedfire.com/linux/rk356x/quick_start/zh/latest/quick_start/name/name.html)

## 3、开启SSH

sudo apt install openssh-server

sudo systemctl start ssh
sudo systemctl enable ssh

sudo systemctl status ssh

## 4、安装Miniforge（arm下的conda）

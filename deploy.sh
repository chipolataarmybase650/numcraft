#!/bin/bash

# NumCraft GitHub 部署脚本
# 使用方法: bash deploy.sh YOUR_GITHUB_TOKEN YOUR_GITHUB_USERNAME

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ "$#" -ne 2 ]; then
    echo -e "${RED}错误: 参数不足${NC}"
    echo "使用方法: bash deploy.sh YOUR_GITHUB_TOKEN YOUR_GITHUB_USERNAME"
    echo ""
    echo "示例: bash deploy.sh ghp_xxxxxxxxxxxx yourusername"
    exit 1
fi

TOKEN=$1
USERNAME=$2
REPO_NAME="numcraft"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  NumCraft GitHub 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 git 是否安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}错误: git 未安装${NC}"
    echo "请先安装 git: https://git-scm.com/downloads"
    exit 1
fi

# 检查是否在项目根目录
if [ ! -f "README.md" ]; then
    echo -e "${RED}错误: 请在项目根目录执行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}步骤 1/7: 初始化 Git 仓库...${NC}"
if [ -d ".git" ]; then
    echo "Git 仓库已存在，跳过初始化"
else
    git init
    echo -e "${GREEN}✓ Git 仓库初始化完成${NC}"
fi

echo ""
echo -e "${YELLOW}步骤 2/7: 配置 Git 用户信息...${NC}"
git config user.email "numcraft@example.com"
git config user.name "NumCraft Bot"
echo -e "${GREEN}✓ Git 用户信息配置完成${NC}"

echo ""
echo -e "${YELLOW}步骤 3/7: 添加文件到暂存区...${NC}"
git add .
echo -e "${GREEN}✓ 文件添加完成${NC}"

echo ""
echo -e "${YELLOW}步骤 4/7: 创建初始提交...${NC}"
git commit -m "Initial commit: NumCraft multi-agent G-code generation system

Features:
- Multi-agent collaborative architecture (5 specialized agents)
- Intelligent feature recognition from natural language
- Automated tool selection and parameter optimization
- Standard G-code generation (FANUC compliant)
- Comprehensive safety validation
- Support for holes, slots, pockets, and contours

Tech stack:
- LangGraph 1.0 for agent orchestration
- LangChain for tool integration
- PostgreSQL for memory persistence

Project initiated: March 2025"
echo -e "${GREEN}✓ 提交创建完成${NC}"

echo ""
echo -e "${YELLOW}步骤 5/7: 创建远程仓库连接...${NC}"
# 移除可能存在的旧远程仓库
git remote remove origin 2>/dev/null || true
# 添加新的远程仓库
git remote add origin https://${TOKEN}@github.com/${USERNAME}/${REPO_NAME}.git
echo -e "${GREEN}✓ 远程仓库连接创建完成${NC}"

echo ""
echo -e "${YELLOW}步骤 6/7: 设置主分支...${NC}"
git branch -M main
echo -e "${GREEN}✓ 主分支设置完成${NC}"

echo ""
echo -e "${YELLOW}步骤 7/7: 推送到 GitHub...${NC}"
git push -u origin main --force
echo -e "${GREEN}✓ 代码推送完成${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "仓库地址: ${GREEN}https://github.com/${USERNAME}/${REPO_NAME}${NC}"
echo ""
echo -e "${YELLOW}重要提醒:${NC}"
echo "1. 请立即撤销您使用的令牌: https://github.com/settings/tokens"
echo "2. 为仓库添加 Topics: cnc, g-code, multi-agent, langgraph"
echo "3. 在仓库设置中添加描述和网站链接"
echo ""
echo -e "${GREEN}部署完成！祝您使用愉快！${NC}"

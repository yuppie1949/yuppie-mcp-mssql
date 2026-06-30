#!/bin/bash
set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== PyPI 发布脚本 ===${NC}"

# 检查 token
if [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo -e "${RED}错误: 未设置 UV_PUBLISH_TOKEN 环境变量${NC}"
    echo "请设置 PyPI API Token:"
    echo "  export UV_PUBLISH_TOKEN='pypi-你的token'"
    exit 1
fi

# 检查版本号
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "${YELLOW}当前版本: ${CURRENT_VERSION}${NC}"

# 提示输入新版本
read -p "请输入新版本号 (当前: ${CURRENT_VERSION}): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    NEW_VERSION=$CURRENT_VERSION
    echo -e "${YELLOW}使用当前版本: ${NEW_VERSION}${NC}"
fi

# 更新版本号
sed -i '' "s/^version = .*/version = \"${NEW_VERSION}\"/" pyproject.toml
echo -e "${GREEN}✓ 版本号已更新为 ${NEW_VERSION}${NC}"

# 确认发布
echo -e "${YELLOW}即将发布到 PyPI:${NC}"
echo "  包名: yuppie-mcp-mssql"
echo "  版本: ${NEW_VERSION}"
read -p "确认发布? (y/N): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${RED}发布已取消${NC}"
    exit 1
fi

# 构建
echo -e "${GREEN}正在构建...${NC}"
uv build

# 发布
echo -e "${GREEN}正在发布到 PyPI...${NC}"
UV_PUBLISH_TOKEN="$UV_PUBLISH_TOKEN" uv publish

echo -e "${GREEN}=== 发布完成 ===${NC}"
echo -e "${GREEN}查看: https://pypi.org/project/yuppie-mcp-mssql/${NC}"

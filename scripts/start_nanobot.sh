#!/bin/bash
# Nanobot 启动脚本
# 包含环境检查和错误处理

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV_PATH="$PROJECT_ROOT/temp_venv"
CONFIG_DIR="$PROJECT_ROOT/config"
DATA_DIR="$PROJECT_ROOT/data"

# 日志函数
log() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查函数
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        log_error "虚拟环境不存在: $VENV_PATH"
        log "请先创建虚拟环境: python -m venv temp_venv"
        return 1
    fi
    
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        log_error "虚拟环境激活脚本不存在"
        return 1
    fi
    
    return 0
}

check_config() {
    if [ ! -d "$CONFIG_DIR" ]; then
        log_error "配置目录不存在: $CONFIG_DIR"
        return 1
    fi
    
    # 检查必要的配置文件
    local config_files=("nanobot_config.yaml")
    
    for config_file in "${config_files[@]}"; do
        if [ ! -f "$CONFIG_DIR/$config_file" ]; then
            log_warn "配置文件不存在: $CONFIG_DIR/$config_file"
            
            # 检查是否有示例文件
            if [ -f "$CONFIG_DIR/examples/${config_file}.example" ]; then
                log "正在从示例文件创建配置文件: examples/${config_file}.example"
                cp "$CONFIG_DIR/examples/${config_file}.example" "$CONFIG_DIR/$config_file"
            elif [ -f "$CONFIG_DIR/examples/${config_file}" ]; then
                log "正在从示例文件创建配置文件: examples/${config_file}"
                cp "$CONFIG_DIR/examples/${config_file}" "$CONFIG_DIR/$config_file"
            else
                log_error "未找到配置文件和示例文件: $config_file"
                return 1
            fi
        fi
    done
    
    return 0
}

check_data_dir() {
    if [ ! -d "$DATA_DIR" ]; then
        log "创建数据目录: $DATA_DIR"
        mkdir -p "$DATA_DIR"
    fi
    
    return 0
}

check_nanobot_command() {
    source "$VENV_PATH/bin/activate" > /dev/null 2>&1
    if ! command -v nanobot &> /dev/null; then
        log_error "nanobot 命令未找到，请重新安装: pip install -e ."
        return 1
    fi
    
    return 0
}

# 启动函数
start_nanobot() {
    log "开始启动 Nanobot..."
    
    # 激活虚拟环境
    log "激活虚拟环境..."
    source "$VENV_PATH/bin/activate"
    
    # 检查是否已安装 nanobot
    if ! command -v nanobot &> /dev/null; then
        log_error "nanobot 命令未找到，正在尝试重新安装..."
        pip install -e .
    fi
    
    # 启动 Nanobot
    log "启动 Nanobot 服务..."
    nanobot gateway
    
    return 0
}

# 主函数
main() {
    log "=== Nanobot 启动脚本 ==="
    
    # 检查系统要求
    log "检查系统要求..."
    
    if ! check_venv; then
        exit 1
    fi
    
    if ! check_config; then
        exit 1
    fi
    
    if ! check_data_dir; then
        exit 1
    fi
    
    if ! check_nanobot_command; then
        exit 1
    fi
    
    # 启动 Nanobot
    if start_nanobot; then
        log "Nanobot 启动成功!"
    else
        log_error "Nanobot 启动失败!"
        exit 1
    fi
}

# 错误处理
trap 'log_error "脚本执行被中断"; exit 1' INT TERM

# 执行主函数
main "$@"

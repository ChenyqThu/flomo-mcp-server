#!/usr/bin/env python3

import requests
import hashlib
import json
from datetime import datetime

def get_flomo_memos(token, latest_slug=None, latest_updated_at=None):
    """
    获取 Flomo 备忘录
    
    Args:
        token: Authorization token (格式: "Bearer your_token_here")
        latest_slug: 分页参数 (可选)
        latest_updated_at: 分页参数 (可选)
    """
    
    # 使用当前真实时间戳
    current_timestamp = str(int(datetime.now().timestamp()))
    
    # 基础参数
    params = {
        "limit": "200",
        "tz": "8:0",
        "timestamp": current_timestamp,  # 关键：使用当前时间
        "api_key": "flomo_web",
        "app_version": "4.0",
        "platform": "web",
        "webp": "1"
    }
    
    # 添加分页参数（如果有）
    if latest_slug and latest_updated_at:
        params.update({
            "latest_slug": latest_slug,
            "latest_updated_at": str(latest_updated_at)
        })
    
    # 生成签名
    salt = "dbbc3dd73364b4084c3a69346e0ce2b2"
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    sign_input = param_str + salt
    sign = hashlib.md5(sign_input.encode("utf-8")).hexdigest()
    params["sign"] = sign
    
    print(f"请求时间戳: {current_timestamp}")
    print(f"签名输入: {sign_input}")
    print(f"生成签名: {sign}")
    print(f"请求参数: {params}")
    
    # 发送请求
    headers = {"Authorization": token}
    
    try:
        response = requests.get(
            "https://flomoapp.com/api/v1/memo/updated/",
            params=params,
            headers=headers
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API响应码: {data.get('code')}")
            print(f"API消息: {data.get('message', 'N/A')}")
            
            if data.get("code") == 0:
                memos = data.get("data", [])
                print(f"成功获取 {len(memos)} 条备忘录")
                
                # 显示第一条备忘录的信息
                if memos:
                    first_memo = memos[0]
                    print(f"\n第一条备忘录:")
                    print(f"- Slug: {first_memo.get('slug')}")
                    print(f"- 创建时间: {first_memo.get('created_at')}")
                    print(f"- 更新时间: {first_memo.get('updated_at')}")
                    print(f"- 内容预览: {first_memo.get('content', '')[:100]}...")
                
                return memos
            else:
                print(f"API错误: {data}")
                return None
        else:
            print(f"HTTP错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def get_all_memos(token):
    """获取所有备忘录（自动处理分页）"""
    all_memos = []
    latest_slug = None
    latest_updated_at = None
    
    while True:
        print(f"\n{'='*50}")
        print(f"获取第 {len(all_memos) // 200 + 1} 页数据...")
        
        memos = get_flomo_memos(token, latest_slug, latest_updated_at)
        
        if not memos:
            print("获取失败或无更多数据")
            break
            
        all_memos.extend(memos)
        
        # 如果这一页数据少于限制数量，说明已经是最后一页
        if len(memos) < 200:
            print("已获取所有数据")
            break
            
        # 设置下一页的分页参数
        last_memo = memos[-1]
        latest_slug = last_memo["slug"]
        latest_updated_at = int(datetime.fromisoformat(last_memo["updated_at"]).timestamp())
        
        print(f"准备获取下一页，latest_slug: {latest_slug}, latest_updated_at: {latest_updated_at}")
    
    print(f"\n总共获取到 {len(all_memos)} 条备忘录")
    return all_memos

# 使用示例
if __name__ == "__main__":
    # 替换为你的实际token
    TOKEN = "Bearer 6782846|pguJkOHgJ21KYW4oHfrEF0syJvHRygKI5a53Mitf"
    
    print("开始获取 Flomo 备忘录...")
    
    # 先获取第一页数据测试
    print("=== 测试获取第一页数据 ===")
    first_page = get_flomo_memos(TOKEN)
    
    if first_page:
        print(f"✅ 成功！获取到 {len(first_page)} 条备忘录")
        
        # 如果需要获取全部数据，取消下面的注释
        # print("\n=== 获取所有数据 ===")  
        # all_memos = get_all_memos(TOKEN)
    else:
        print("❌ 获取失败，请检查token和网络连接")
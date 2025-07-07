import openai
import os
import json
from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv
import asyncio

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()
@app.get("/")
async def root():
    return {"message": "👋 Welcome to the Budget Review API. Visit /docs to try it."}

@app.post("/review/")
async def review_financial_profile(file: UploadFile):
    contents = await file.read()
    data = json.loads(contents.decode("utf-8"))

    profile = data["profile"]
    thresholds = data.get("thresholds", {})

    #Đọc thông tin chính
    type_ = profile["type"]
    income = profile["income"]
    limit = profile["currentLimit"]
    expense = abs(profile["expense"])

    # Chuẩn bị dữ liệu nợ
    depts = profile.get("depts", [])
    dept_text = "\n".join([
        f"- {d['name']}: đã trả {d['currentAmount']:,} / {d['target']:,}đ (hạn: {d['deadline']})"
        for d in depts
    ]) if depts else "Không có nợ"

    # Chuẩn bị dữ liệu giao dịch
    transactions = profile.get("transactions", [])
    trans_text = "\n".join([
        f"- {t['category']}: chi {abs(t['totalExpense']):,}đ" +
        (f", thu {t['totalIncome']:,}đ" if t["totalIncome"] else "")
        for t in transactions
    ]) if transactions else "Không có giao dịch"

    #Giới hạn
    max_disc = thresholds.get("max_discretionary_pct", 0.2)
    max_shop = thresholds.get("suggested_max_shopping_pct", 0.05)

    #Tạo prompt
    prompt = f"""
Dưới đây là thông tin tài chính của người dùng:

- Loại đánh giá: {type_.lower()}
- Thu nhập: {income:,}đ
- Hạn mức chi tiêu: {limit:,}đ
- Chi tiêu hàng ngày: {expense:,}đ

💳 Nợ hiện tại:
{dept_text}

📊 Các khoản chi tiêu theo danh mục:
{trans_text}

⚠️ Giới hạn gợi ý:
- Tối đa {int(max_disc * 100)}% thu nhập cho chi tiêu không thiết yếu (mua sắm, giải trí)
- Tối đa {int(max_shop * 100)}% cho thời trang

👉 Hãy đánh giá mức chi tiêu của người dùng:
- Tổng quan: có vượt hạn mức không? có chi tiêu quá tay không?
- Gợi ý cụ thể: nên giảm chi tiêu ở đâu? mục nào ổn?
- Đánh giá tiến độ trả nợ
- Gợi ý cải thiện tài chính

Trả lời bằng tiếng Việt, giọng nhẹ nhàng và hữu ích.
"""
    
    # Gọi OpenAI GPT-4o-mini
    response = openai.ChatCompletion.create(
        model='gpt-4o-mini',
        messages=[
            {"role": "system", "content": "Bạn là một chuyên gia tài chính, giúp người dùng cải thiện tình hình tài chính của họ, nói Tiếng Việt"},
            {"role": "user", "content": prompt}
        ]
    )

    return response['choices'][0]['message']['content']
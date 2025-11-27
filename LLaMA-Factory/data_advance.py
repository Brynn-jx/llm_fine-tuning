import json
import random
import re
from collections import defaultdict

# ================= 配置区域 =================
INPUT_FILE = "data/movies_sft2/llama_factory_movie_train.jsonl"
OUTPUT_FILE = "data/movies_sft2/llama_factory_movie_logic_fixed.jsonl"
TARGET_TOTAL_SAMPLES = 5000  # 生成数据量

# ================= 1. 严格的语料库 =================

# 评分模板 (Prompt 必须对应 Answer 的属性)
PROMPTS_RATING_STRICT = [
    "I only watch high-quality movies. Recommend a {genre} movie with rating higher than {threshold}.",
    "Show me a {genre} film rated above {threshold} on IMDb.",
    "Do you have any {genre} movies with a score greater than {threshold}?",
    "Recommend a highly-rated {genre} movie (>{threshold})."
]

# 年份模板
PROMPTS_YEAR_STRICT = [
    "Recommend a {genre} movie released after {year}.",
    "I want to see a recent {genre} film (post-{year}).",
    "Any {genre} movies from {year} or later?",
    "Can you list a {genre} movie released since {year}?"
]

# 详情模板
PROMPTS_DETAIL = [
    "Tell me more about it.",
    "What is the plot?",
    "Can you give me the brief intro?",
    "What makes this movie special?"
]

# 机器人开场白
BOT_INTROS = [
    "Here is a recommendation that fits your criteria:\n\n",
    "You might enjoy this one:\n\n",
    "Check this out:\n\n",
    "Based on your request:\n\n"
]


# ================= 2. 增强型解析器 (解决空内容问题) =================

def parse_movie_data(text):
    """
    从原始文本中提取结构化数据。
    增加了严格的非空检查。
    """
    movies = []
    # 切割块
    chunks = re.split(r'(?m)^\d+\.\s+(?=.*\(IMDb)', text)

    for chunk in chunks:
        if not chunk.strip() or "(IMDb" not in chunk: continue

        try:
            # 1. 提取头信息
            header_match = re.search(r"^(.*?)\s+\(IMDb\s+([\d\.]+),\s+(\d{4})\)", chunk.strip(), re.MULTILINE)
            if not header_match: continue

            title = header_match.group(1).strip()
            rating = float(header_match.group(2))
            year = int(header_match.group(3))

            # 2. 提取简介 (增加非空校验)
            intro_match = re.search(r"Brief intro:(.*?)(\nKey highlights|\nKeywords|$)", chunk, re.DOTALL)
            intro = intro_match.group(1).strip() if intro_match else ""

            # 3. 提取看点
            high_match = re.search(r"Key highlights:(.*?)(\nKeywords|$)", chunk, re.DOTALL)
            highlights = high_match.group(1).strip() if high_match else ""

            # 关键修复：如果简介或看点太短，视为脏数据，直接丢弃
            if len(intro) < 5 or len(highlights) < 2:
                # print(f"Skipping bad data: {title}")
                continue

            # 重新组装标准文本
            full_text = f"{title} (IMDb {rating}, {year})\nBrief intro: {intro}\nKey highlights: {highlights}"

            movies.append({
                "title": title,
                "rating": rating,
                "year": year,
                "intro": intro,
                "highlights": highlights,
                "full_text": full_text
            })
        except:
            continue
    return movies


def get_genre(text):
    genres = ["Comedy", "Action", "Thriller", "Romance", "Drama", "Horror", "Sci-Fi", "Adventure", "Crime", "Mystery",
              "Fantasy", "Animation", "Documentary", "War", "History", "Western", "Family", "Music", "TV Movie"]
    for g in genres:
        if g.lower() in text.lower(): return g
    return "Movie"


# ================= 3. 逆向生成逻辑 =================

def main():
    print(f" 启动严格逻辑生成脚本，目标: {TARGET_TOTAL_SAMPLES} 条...")

    # 1. 构建清洗后的电影库
    movie_kb = defaultdict(list)
    unique_ids = set()

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                msgs = item.get("conversations", [])
                if len(msgs) < 2: continue

                genre = get_genre(msgs[0]['value'])
                movies = parse_movie_data(msgs[1]['value'])

                for m in movies:
                    # 唯一标识
                    uid = f"{m['title']}_{m['year']}"
                    if uid not in unique_ids:
                        movie_kb[genre].append(m)
                        unique_ids.add(uid)
            except:
                continue

    total_movies = sum(len(v) for v in movie_kb.values())
    print(f"有效电影库存: {total_movies} 部。开始生成...")

    # 2. 生成逻辑数据
    new_dataset = []
    genre_list = list(movie_kb.keys())

    for _ in range(TARGET_TOTAL_SAMPLES):
        # 随机选一个有库存的类别
        valid_genres = [g for g in genre_list if len(movie_kb[g]) > 0]
        if not valid_genres: break
        genre = random.choice(valid_genres)
        pool = movie_kb[genre]

        # 随机选择一种训练模式
        mode = \
        random.choices(["logic_year", "logic_rating", "simple_batch", "detail_chain"], weights=[25, 25, 25, 25], k=1)[0]

        conversations = []
        conversations.append({"from": "system", "value": "You are a helpful movie recommendation assistant."})

        # --- 模式 A: 严格年份逻辑 (Logic Year) ---
        # 逻辑：先选电影，再根据电影年份生成问题。
        if mode == "logic_year":
            m = random.choice(pool)
            # 生成一个比电影实际年份小的基准年 (例如电影是2016，我们问“推荐2010年后的”)
            # 确保逻辑成立: 电影Year > QueryYear
            query_year = m['year'] - random.randint(1, 5)
            # 稍微规整一下年份 (例如变成 2010, 2015)
            if query_year > 2010:
                query_year = 2010
            elif query_year > 2000:
                query_year = 2000

            q = random.choice(PROMPTS_YEAR_STRICT).format(genre=genre, year=query_year)
            a = f"{random.choice(BOT_INTROS)}1. {m['full_text']}"
            conversations += [{"from": "human", "value": q}, {"from": "assistant", "value": a}]

        # --- 模式 B: 严格评分逻辑 (Logic Rating) ---
        elif mode == "logic_rating":
            m = random.choice(pool)
            # 生成一个比电影实际评分低的基准分 (例如电影 7.5，我们问“推荐大于 6.0 的”)
            if m['rating'] < 5.0: continue  # 评分太低就不生成高分推荐语料了

            query_threshold = int(m['rating']) - 1  # 向下取整再减1，保证肯定是大于关系
            if query_threshold < 5: query_threshold = 5

            q = random.choice(PROMPTS_RATING_STRICT).format(genre=genre, threshold=query_threshold)
            a = f"Here is a highly rated movie (IMDb {m['rating']}):\n\n1. {m['full_text']}"
            conversations += [{"from": "human", "value": q}, {"from": "assistant", "value": a}]

        # --- 模式 C: 批量列表 (Batch) ---
        elif mode == "simple_batch":
            n = random.randint(2, 3)
            if len(pool) < n: continue
            batch = random.sample(pool, n)

            q = f"Recommend {n} {genre} movies."
            # 强制重新编号，确保格式 1. 2. 3.
            lines = []
            for i, m in enumerate(batch, 1):
                lines.append(f"{i}. {m['full_text']}")

            a = f"Here are {n} movies for you:\n\n" + "\n\n".join(lines)
            conversations += [{"from": "human", "value": q}, {"from": "assistant", "value": a}]

        # --- 模式 D: 详情追问 (Detail Chain) ---
        elif mode == "detail_chain":
            m = random.choice(pool)

            # 轮次 1: 推荐
            q1 = f"Recommend a {genre} movie."
            a1 = f"I recommend:\n\n1. {m['full_text']}"

            # 轮次 2: 追问详情 (强迫模型只输出简介)
            q2 = random.choice(PROMPTS_DETAIL)
            # 答案只包含 intro，不包含 Title 和 Rating，让模型学会区分字段
            a2 = f"{m['intro']}"

            conversations += [
                {"from": "human", "value": q1},
                {"from": "assistant", "value": a1},
                {"from": "human", "value": q2},
                {"from": "assistant", "value": a2}
            ]

        if len(conversations) > 1:
            new_dataset.append({"conversations": conversations})

    # 4. 写入
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in new_dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"修复版数据已生成: {OUTPUT_FILE}")
    print(f"总条数: {len(new_dataset)}")
    print(
        "逻辑修复点：\n1. 剔除了 Brief intro 为空的数据\n2. 确保年份/评分提问与电影实际属性 100% 匹配\n3. 修复了序号和列表逻辑")


if __name__ == "__main__":
    main()
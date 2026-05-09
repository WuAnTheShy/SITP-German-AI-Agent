import json
d = json.load(open('backend/evals/results/v3_student_20260508_190230.json', encoding='utf-8'))
cases = [x for x in d['details'] if x['category'] == 'general_chat']
for c in cases:
    print(f"\n[{c['id']}] query: {c['query']}")
    print(f"  actual_tools: {c['actual_tools']}")
    print(f"  judge: {c['judge']['overall_score']}")
    print(f"  reasoning: {c['judge']['reasoning']}")
    print(f"  reply: {c['reply_preview'][:200]}")

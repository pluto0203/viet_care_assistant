# VietCare Assistant — Agent Upgrade Design

**Date:** 2026-06-04  
**Status:** Approved  
**Scope:** Nâng cấp từ LLM chatbot đơn thuần thành Tool-calling Agent với multi-step reasoning

---

## 1. Mục tiêu

Biến VietCare từ pipeline RAG cố định thành Agent thực thụ: LLM tự quyết định khi nào cần tìm KB, khi nào cần tìm bệnh viện, và có thể phối hợp nhiều tool trong một câu hỏi.

---

## 2. Kiến trúc

### Trước
```
Router → ChatService → LLMService (RAG cố định + LLM)
```

### Sau
```
Router → ChatService → AgentService → OpenRouter (function calling)
                              ↓
                         Tool Dispatcher
                         ├── KBSearchTool   (FAISS RAG)
                         └── HospitalTool   (Nominatim + Overpass API)
```

### Nguyên tắc thiết kế
- `LLMService` giữ nguyên, expose `_retrieve_context` cho `KBSearchTool`
- `AgentService` là layer mới duy nhất, chứa agent loop
- `ChatService` gọi `AgentService` thay vì `LLMService` trực tiếp
- API endpoints không thay đổi — frontend và tests hiện tại không cần sửa

---

## 3. Files thay đổi

```
app/services/
├── llm.py               ← đổi _retrieve_context thành public retrieve_context
├── agent_service.py     ← MỚI: agent loop
├── chat_service.py      ← sửa: dùng AgentService
└── tools/
    ├── __init__.py      ← MỚI
    ├── kb_tool.py       ← MỚI: search_knowledge_base tool
    └── hospital_tool.py ← MỚI: find_nearby_hospitals tool
```

---

## 4. Tool Definitions

### Tool 1: `search_knowledge_base`

**Khi nào dùng:** User hỏi về triệu chứng, bệnh, thuốc, sức khỏe tâm thần, thông tin y tế chung.

**Schema:**
```json
{
  "name": "search_knowledge_base",
  "description": "Tìm kiếm thông tin y tế trong knowledge base nội bộ. Dùng cho câu hỏi về triệu chứng, bệnh lý, thuốc, sức khỏe tâm thần.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Câu hỏi hoặc từ khóa cần tìm kiếm"},
      "collection_id": {"type": "integer", "description": "ID của knowledge base collection"}
    },
    "required": ["query", "collection_id"]
  }
}
```

**Execute:** Gọi `LLMService.retrieve_context(query, db, collection_id)` → trả context text + sources.

---

### Tool 2: `find_nearby_hospitals`

**Khi nào dùng:** User hỏi tìm bệnh viện, phòng khám, cơ sở y tế gần địa điểm nào đó.

**Schema:**
```json
{
  "name": "find_nearby_hospitals",
  "description": "Tìm bệnh viện và phòng khám gần một địa điểm. Dùng khi user cần tìm cơ sở y tế gần.",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {"type": "string", "description": "Tên địa điểm, ví dụ: 'quận 1 HCM', 'Hoàn Kiếm Hà Nội'"},
      "radius_km": {"type": "integer", "description": "Bán kính tìm kiếm tính bằng km", "default": 2},
      "limit": {"type": "integer", "description": "Số kết quả tối đa trả về", "default": 5}
    },
    "required": ["location"]
  }
}
```

**Execute:**
1. Nominatim geocoding: `location` string → lat/lng (OSM, miễn phí, không cần key)
2. Overpass API query: `amenity=hospital` hoặc `amenity=clinic` trong `radius_km`
3. Trả về list: `[{name, address, distance_km}]`, sắp xếp gần nhất trước

---

## 5. Agent Loop

```python
async def run(query, collection_id, db, history, stream=False):
    messages = build_messages(system_prompt, history, query)
    tools = [KB_TOOL_SCHEMA, HOSPITAL_TOOL_SCHEMA]
    
    for iteration in range(MAX_ITERATIONS):  # MAX_ITERATIONS = 5
        response = openrouter.chat(messages, tools=tools)
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = execute_tool(tool_call, collection_id, db)
                messages.append(tool_result_message(tool_call.id, result))
            continue  # loop back
        
        return response.content  # final answer
    
    return "Xin lỗi, tôi không thể xử lý yêu cầu này."
```

**Giới hạn:** Tối đa 5 vòng lặp để tránh infinite loop.

**Streaming:** Tool execution chạy synchronously, text chunks được yield sau khi tool results đã có.

---

## 6. API Endpoints — Không thay đổi

| Endpoint | Thay đổi |
|---|---|
| `POST /chat/{id}/conversations` | Không |
| `POST /chat/{id}/conversations/{cid}/messages` | Engine bên trong: `LLMService` → `AgentService` |
| `POST /chat/{id}/conversations/{cid}/stream` | Engine bên trong: `LLMService` → `AgentService` |
| Tất cả endpoints khác | Không |

Frontend Streamlit và test suite hiện tại không cần sửa.

---

## 7. External Services

| Service | Mục đích | Auth | Chi phí |
|---|---|---|---|
| Nominatim (OSM) | Geocoding địa chỉ → lat/lng | Không cần | Miễn phí |
| Overpass API | Tìm amenities trong bán kính | Không cần | Miễn phí |
| OpenRouter | LLM + function calling | API key hiện tại | Giữ nguyên |

**Rate limit Nominatim:** 1 request/giây — cần thêm `User-Agent` header hợp lệ theo policy của OSM.

---

## 8. Error Handling

- Tool fails → agent nhận error message → tiếp tục với thông tin có sẵn, không crash
- Nominatim không tìm được địa điểm → trả về message thân thiện yêu cầu user cung cấp rõ hơn
- Overpass timeout → fallback message gợi ý tìm trên Google Maps
- Agent loop vượt MAX_ITERATIONS → trả về câu trả lời chung chung kèm xin lỗi

---

## 9. Out of Scope

- Multi-agent (nhiều agent phối hợp) — không trong scope này
- Frontend thay đổi — giữ nguyên Streamlit
- Tool mới ngoài 2 tools đã định nghĩa
- Caching kết quả hospital search

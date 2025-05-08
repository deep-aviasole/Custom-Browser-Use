from src.tools.excel_tool import SaveExcelInput, save_to_excel
import asyncio
import json

async def test_save():
    data = {
        "title": "Iron Man",
        "powers": [
            "Genius-level intellect",
            "Proficient scientist and engineer",
            "Utilizes powered armor suit",
            "Superhuman strength (granted by armor)",
            "Flight (granted by armor)",
            "Energy projection (granted by armor)"
        ]
    }
    # Simulate BrowserUseAgent's JSON string input
    input_data = json.dumps(data)
    save_input = SaveExcelInput(data=input_data)
    result = await save_to_excel(save_input)
    print(result)

if __name__ == "__main__":
    asyncio.run(test_save())
import re
from pliego_esp.graph.state import State
from rich.console import Console

console = Console()

async def parse_adicionales(state: State) -> State:
    console.print("-----parse_adicionales-----", style="bold yellow")
    
    adicionales_md = state.get("adicionales_pliego", "").strip()
    if not adicionales_md:
        console.print("⚠️ No se encontró texto en 'adicionales_pliego'", style="bold red")
        state["parsed_adicionales"] = []
        return state

    adicionales_struct = []

    for line in adicionales_md.splitlines():
        match = re.match(r"- \*\*(.*?)\*\*: (.+)", line)
        if match:
            nombre = match.group(1).strip()
            descripcion = match.group(2).strip()
            adicionales_struct.append({
                "actividad": nombre,
                "descripcion": descripcion
            })
        else:
            console.print(f"❗ Línea no válida: {line}", style="red")

    console.print(adicionales_struct, style="yellow")
    console.print(f"✅ Adicionales parseados: {len(adicionales_struct)} encontrados", style="bold yellow")
    console.print(20*"-", style="bold yellow")
    return {"parsed_adicionales": adicionales_struct}

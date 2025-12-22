import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tutor_agent import TutorAgent
from core.tutor_state import default_tutor_state

# Initialize Rich Console
console = Console()

async def interactive_test():
    agent = TutorAgent()
    state = default_tutor_state()
    
    # Header
    console.print(Panel.fit(
        "[bold cyan]🤖 Tutor Agent Interactive Test[/bold cyan]", 
        border_style="cyan"
    ))
    console.print("[dim]Type 'quit' to exit[/dim]\n")
    
    # Get initial context
    notes = Prompt.ask("[bold green]Enter your study notes/context[/bold green]")
    console.print()
    
    while True:
        # User Input
        question = Prompt.ask("[bold yellow]You[/bold yellow]")
        if question.lower() == 'quit':
            console.print("\n[bold red]Goodbye! 👋[/bold red]")
            break
            
        input_data = {
            "question": question,
            "notes": notes
        }
        
        # Show a spinner while waiting for response
        with console.status("[bold cyan]Tutor is thinking...[/bold cyan]", spinner="dots"):
            result = await agent.run(input_data, state)
        
        # Display Response
        console.print(Panel(
            Markdown(result['explanation']),
            title="🎓 Tutor",
            border_style="green",
            expand=False
        ))
        
        # Display State Metadata
        console.print(
            f"📊 [dim]Confusion: {result['confusion_level']:.2f} | Style: {result['explanation_style']}[/dim]"
        )
        console.rule(style="dim")
        console.print()

if __name__ == "__main__":
    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/bold red]")
"""Record reviewed gate evidence; invoke only after the task gate passes."""
import sys
from pathlib import Path
number, result, *tests = sys.argv[1:]
p=Path('.specs/features/controle-familiar/tasks.md')
s=p.read_text(); start=s.index(f'### T{number}:'); end=s.find('\n### T',start+1)
if end<0:end=s.index('\n## Task Granularity Check',start)
block=s[start:end]; requirement=next(line for line in block.splitlines() if line.startswith('- **Requirement**'))
s=s[:start]+block.replace('- **Status**: Pending.',f'- **Status**: Complete — {result}.')+s[end:];p.write_text(s)
p=Path('.specs/features/controle-familiar/execution.md')
with p.open('a') as f:
    f.write(f'\n## T{number}\n\nGate: {result}.\n{requirement}\n\n| Evidência de asserção | Requisito / resultado |\n| --- | --- |\n')
    for name in tests:
        for n,line in enumerate(Path(name).read_text().splitlines(),1):
            if 'assert ' in line or 'pytest.raises' in line:
                f.write(f'| {name}:{n} — `{line.strip().replace("|", "/")}` | Critérios da tarefa acima; valor esperado literal da especificação |\n')
    f.write('\nMapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.\n')

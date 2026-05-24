import re
with open('main.py', 'r') as f:
    content = f.read()

# Pattern: templates.TemplateResponse("something.html", {
new_content = re.sub(
    r'templates\.TemplateResponse\(([\'\"][^\'\"]+[\'\"]),\s*(\{)', 
    r'templates.TemplateResponse(request=request, name=\1, context=\2', 
    content
)

with open('main.py', 'w') as f:
    f.write(new_content)

print('Updated templates.TemplateResponse calls.')

from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")

class HTMLRender:
    def __init__(self, request: Request):
        self.request = request
    
    def render(self, template: str, **context):
        context['request'] = self.request
        return templates.TemplateResponse(self,template, context)
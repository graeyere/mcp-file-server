# MCP in four parts

## 1 Tools

Tools are actions the model can invoke, such as write_file. They are model-controlled, which means they can change the outside world. Each tool is defined by a name, a description and a JSON input schema.

## 2 Resources

Resources are read-only context addressed by a URI, such as file:///projects/demo/PROJECT_STATE.md. They are application-controlled, so the host decides what to attach.

## 3 Prompts

Prompts are reusable message templates that the user picks, often as slash commands such as /review-code. They are user-controlled. They give a repeatable workflow with fixed wording.

## 4 Transports

stdio runs the server as a subprocess of the host on the same machine. Streamable HTTP serves it at a URL so any client that can reach it can connect. This means authentication must be added.

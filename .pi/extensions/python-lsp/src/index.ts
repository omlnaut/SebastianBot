import { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn, ChildProcess } from "child_process";
import * as rpc from "vscode-jsonrpc/node.js";
import { Type } from "@sinclair/typebox";
import path from "path";
import { readFile } from "fs/promises";

export default function (pi: ExtensionAPI) {
    let connection: rpc.MessageConnection | null = null;
    let childProcess: ChildProcess | null = null;
    const openedDocs = new Set<string>();

    async function withTimeout<T>(promise: Promise<T>, timeoutMs: number, label: string): Promise<T> {
        return Promise.race([
            promise,
            new Promise<T>((_, reject) =>
                setTimeout(() => reject(new Error(`Timeout: ${label} after ${timeoutMs}ms`)), timeoutMs)
            ),
        ]);
    }

    async function ensureLSP(cwd: string) {
        if (connection) return connection;

        const serverPath = "/usr/local/bin/pyright-langserver";

        childProcess = spawn(serverPath, ["--stdio"], {
            cwd,
        });

        childProcess.stderr?.on("data", (data) => {
            // console.error(`LSP Stderr: ${data}`);
        });

        connection = rpc.createMessageConnection(
            new rpc.StreamMessageReader(childProcess.stdout!),
            new rpc.StreamMessageWriter(childProcess.stdin!),
            undefined,
            {
                encoding: "utf-8",
                canUndefined: true,
            }
        );

        connection.listen();

        const initializeParams = {
            processId: process.pid,
            rootUri: `file://${cwd}`,
            capabilities: {
                textDocument: {
                    documentSymbol: {
                        hierarchicalDocumentSymbolSupport: true,
                    },
                },
            },
            workspaceFolders: [
                {
                    uri: `file://${cwd}`,
                    name: path.basename(cwd),
                },
            ],
        };

        await withTimeout(
            connection.sendRequest("initialize", initializeParams),
            5000,
            "LSP Initialize"
        );
        connection.sendNotification("initialized", {});
        return connection;
    }

    async function ensureDidOpen(conn: rpc.MessageConnection, absPath: string) {
        const uri = `file://${absPath}`;
        if (openedDocs.has(uri)) return;

        const text = await readFile(absPath, "utf-8");
        conn.sendNotification("textDocument/didOpen", {
            textDocument: {
                uri,
                languageId: "python",
                version: 1,
                text,
            },
        });
        openedDocs.add(uri);
    }

    pi.registerTool({
        name: "python_lsp_definition",
        label: "Python LSP Definition",
        description: "Preferred for Python navigation: find the definition of a symbol in Python code",
        parameters: Type.Object({
            path: Type.String({ description: "Relative path to the python file" }),
            line: Type.Number({ description: "Line number (0-indexed)" }),
            character: Type.Number({ description: "Character position (0-indexed)" }),
        }),
        async execute(toolCallId, params, signal, onUpdate, ctx) {
            try {
                const conn = await ensureLSP(ctx.cwd);
                const absPath = path.resolve(ctx.cwd, params.path);
                
                await ensureDidOpen(conn, absPath);

                const result = await withTimeout(
                    conn.sendRequest("textDocument/definition", {
                        textDocument: { uri: `file://${absPath}` },
                        position: { line: params.line, character: params.character },
                    }),
                    5000,
                    "LSP Definition"
                );

                return {
                    content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
                    details: { result }
                };
            } catch (err: any) {
                return {
                    content: [{ type: "text", text: `Error: ${err.message}` }],
                    isError: true
                };
            }
        }
    });

    pi.registerTool({
        name: "python_lsp_references",
        label: "Python LSP References",
        description: "Preferred for Python navigation: find references of a symbol in Python code",
        parameters: Type.Object({
            path: Type.String({ description: "Relative path to the python file" }),
            line: Type.Number({ description: "Line number (0-indexed)" }),
            character: Type.Number({ description: "Character position (0-indexed)" }),
        }),
        async execute(toolCallId, params, signal, onUpdate, ctx) {
            try {
                const conn = await ensureLSP(ctx.cwd);
                const absPath = path.resolve(ctx.cwd, params.path);
                
                await ensureDidOpen(conn, absPath);

                const result = await withTimeout(
                    conn.sendRequest("textDocument/references", {
                        textDocument: { uri: `file://${absPath}` },
                        position: { line: params.line, character: params.character },
                        context: { includeDeclaration: true },
                    }),
                    5000,
                    "LSP References"
                );

                return {
                    content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
                    details: { result }
                };
            } catch (err: any) {
                return {
                    content: [{ type: "text", text: `Error: ${err.message}` }],
                    isError: true
                };
            }
        }
    });

    pi.registerTool({
        name: "python_lsp_symbols",
        label: "Python LSP Symbols",
        description: "Preferred for Python exploration: list symbols in a Python file (functions, classes, methods)",
        parameters: Type.Object({
            path: Type.String({ description: "Relative path to the python file" }),
        }),
        async execute(toolCallId, params, signal, onUpdate, ctx) {
            try {
                const conn = await ensureLSP(ctx.cwd);
                const absPath = path.resolve(ctx.cwd, params.path);
                
                await ensureDidOpen(conn, absPath);

                const result = await withTimeout(
                    conn.sendRequest("textDocument/documentSymbol", {
                        textDocument: { uri: `file://${absPath}` },
                    }),
                    5000,
                    "LSP Symbols"
                );

                return {
                    content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
                    details: { result }
                };
            } catch (err: any) {
                return {
                    content: [{ type: "text", text: `Error: ${err.message}` }],
                    isError: true
                };
            }
        }
    });

    pi.on("session_shutdown", async () => {
        if (connection) {
            connection.dispose();
        }
        openedDocs.clear();
        if (childProcess) {
            childProcess.kill();
        }
    });
}

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { chatWithContract } from "@/lib/api/contracts";
import type { Contract, ContractChatMessage, ContractChatSource } from "@/lib/types/contract";
import { useMutation } from "@tanstack/react-query";
import { Bot, Loader2, Search, Send, User } from "lucide-react";
import { toast } from "sonner";

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  sources?: ContractChatSource[];
  usedWeb?: boolean;
}

interface ContractAIChatProps {
  contracts: Contract[];
}

export function ContractAIChat({ contracts }: ContractAIChatProps) {
  const [selectedContractId, setSelectedContractId] = useState<string>(contracts[0]?.id || "");
  const [question, setQuestion] = useState("");
  const [includeWeb, setIncludeWeb] = useState(false);
  const [messages, setMessages] = useState<ChatTurn[]>([]);

  useEffect(() => {
    if (!contracts.length) {
      setSelectedContractId("");
      return;
    }
    if (!selectedContractId || !contracts.some((contract) => contract.id === selectedContractId)) {
      setSelectedContractId(contracts[0].id);
    }
  }, [contracts, selectedContractId]);

  const selectedContract = useMemo(
    () => contracts.find((contract) => contract.id === selectedContractId),
    [contracts, selectedContractId],
  );

  const chatMutation = useMutation({
    mutationFn: async (payload: { question: string; includeWeb: boolean; history: ContractChatMessage[] }) => {
      if (!selectedContractId) {
        throw new Error("Select a contract first.");
      }
      return chatWithContract(selectedContractId, payload);
    },
    onSuccess: (response) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          usedWeb: response.usedWeb,
        },
      ]);
    },
    onError: (err: Error) => {
      const message = err.message || "Failed to get AI response";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `I couldn't answer that right now: ${message}`,
        },
      ]);
      toast.error(message);
    },
  });

  const handleSend = () => {
    const trimmed = question.trim();
    if (!trimmed) return;
    if (!selectedContractId) {
      toast.error("Please select a contract first.");
      return;
    }

    const history: ContractChatMessage[] = messages
      .slice(-10)
      .map((item) => ({ role: item.role, content: item.content }));

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setQuestion("");
    chatMutation.mutate({
      question: trimmed,
      includeWeb,
      history,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          Contract AI Assistant
        </CardTitle>
        <CardDescription>
          Ask contract-specific questions and optionally enrich with web research for legal and regulatory context.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
          <div className="space-y-1">
            <label className="text-sm font-medium">Contract</label>
            <select
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              value={selectedContractId}
              onChange={(e) => {
                setSelectedContractId(e.target.value);
                setMessages([]);
              }}
            >
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>
                  {contract.name}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm mt-6 md:mt-0">
            <Checkbox
              checked={includeWeb}
              onCheckedChange={(checked) => setIncludeWeb(checked === true)}
            />
            <span className="inline-flex items-center gap-1">
              <Search className="h-3.5 w-3.5" />
              Include Web Context
            </span>
          </label>
        </div>

        <div className="rounded-md border p-3 h-[380px] overflow-y-auto space-y-3 bg-muted/20">
          {messages.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Ask about payment terms, timelines, reimbursement clauses, termination language, or legal implications.
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`rounded-md p-3 text-sm ${
                  message.role === "user" ? "bg-primary text-primary-foreground ml-8" : "bg-background border mr-8"
                }`}
              >
                <div className="mb-1 flex items-center gap-2 font-medium">
                  {message.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                  {message.role === "user" ? "You" : "Contract Assistant"}
                </div>
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Sources</p>
                    {message.sources.slice(0, 6).map((source, sourceIndex) => (
                      <div key={`${source.title}-${sourceIndex}`} className="rounded border p-2 text-xs bg-muted/30">
                        <p className="font-medium">
                          {source.sourceType === "web" ? "Web" : "Contract"}: {source.title}
                        </p>
                        <p className="text-muted-foreground">{source.snippet}</p>
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline break-all"
                          >
                            {source.url}
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {message.usedWeb && (
                  <p className="mt-2 text-[11px] text-muted-foreground">
                    This response included optional web context in addition to contract text.
                  </p>
                )}
              </div>
            ))
          )}
        </div>

        <div className="space-y-3">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={
              selectedContract
                ? `Ask about "${selectedContract.name}"...`
                : "Select a contract and ask a question..."
            }
            rows={4}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                if (!chatMutation.isPending) handleSend();
              }
            }}
          />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Responses are informational only and not legal advice.
            </p>
            <Button onClick={handleSend} disabled={chatMutation.isPending || !question.trim() || !selectedContractId}>
              {chatMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Thinking...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Ask AI
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

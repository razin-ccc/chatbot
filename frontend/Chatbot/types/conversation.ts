export type Conversation = {
  id: string;
  title: string | null;
  created_at: string;
};

export type StoredMessage = {
  id: string;
  role: "user" | "model";
  content: string;
  created_at: string;
};

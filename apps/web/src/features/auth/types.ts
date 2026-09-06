export type User = {
  id: string;
  email: string;
  role: "OWNER" | "ADMIN" | "VIEWER";
};

export type SystemStatus = {
  api: "available";
  postgresql: "available";
  redis: "ready";
};

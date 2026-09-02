import { createFileRoute } from "@tanstack/react-router";
import { HomePage } from "@/components/razor";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "RazorGrowth AI — Shop smarter with AI" },
      { name: "description", content: "Discover products with explainable AI recommendations and user-confirmed commerce actions." },
      { property: "og:title", content: "RazorGrowth AI — Shop smarter with AI" },
      { property: "og:description", content: "Discover products with explainable AI recommendations and user-confirmed commerce actions." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HomePage,
});
import re
from typing import List, Set


class SkillExtractor:
    def __init__(self):
        self._registry = {
            "javascript": ["javascript", "js", "ecmascript", "es6"],
            "typescript": ["typescript", "ts"],
            "react": ["react", "reactjs", "react.js"],
            "node.js": ["node", "nodejs", "node.js"],
            "python": ["python"],
            "go": ["go", "golang"],
            "rust": ["rust"],
            "aws": ["aws", "amazon web services"],
            "docker": ["docker"],
            "kubernetes": ["kubernetes", "k8s"],
            "postgresql": ["postgresql", "postgres", "psql"],
            "mongodb": ["mongodb", "mongo"],
            "graphql": ["graphql", "gql"],
            "next.js": ["nextjs", "next.js"],
            "tailwind css": ["tailwind", "tailwindcss"],
            "vue.js": ["vue", "vuejs", "vue.js"],
            "angular": ["angular"],
            "ruby": ["ruby", "rails"],
            "java": ["java"],
            "c#": ["c#", "csharp", ".net"],
            "swift": ["swift"],
            "kotlin": ["kotlin"],
            "flutter": ["flutter"],
            "react native": ["react native"],
            "terraform": ["terraform"],
            "ci/cd": ["ci/cd", "cicd"],
            "machine learning": ["ml", "machine learning", "ai"],
            "data science": ["data science"],
            "system design": ["system design"],
            "microservices": ["microservices"],
            "redis": ["redis"],
            "kafka": ["kafka"],
            "rabbitmq": ["rabbitmq"],
            "elasticsearch": ["elasticsearch", "elastic", "elk"],
            "sql": ["sql", "mysql", "mariadb"],
            "git": ["git", "github", "gitlab"],
            "linux": ["linux", "unix", "bash", "shell"],
        }

    @property
    def known_slugs(self) -> List[str]:
        return list(self._registry.keys())

    def extract(self, tags: List[str], description: str) -> List[str]:
        found: Set[str] = set()
        corpus = " ".join(tags).lower() + " " + description.lower()

        for slug, aliases in self._registry.items():
            for alias in aliases:
                pattern = r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])"
                if re.search(pattern, corpus):
                    found.add(slug)
                    break

        return sorted(found)

    def extract_from_tags(self, tags: List[str]) -> List[str]:
        found: Set[str] = set()
        tag_text = " ".join(tags).lower()

        for slug, aliases in self._registry.items():
            for alias in aliases:
                if alias in tag_text:
                    found.add(slug)
                    break

        return sorted(found)

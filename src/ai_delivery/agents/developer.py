"""Developer agent for generating code."""

from ai_delivery.models.task_spec import TaskSpec
from ai_delivery.models.generated_artifact import GeneratedArtifact


class DeveloperAgent:
    """Agent responsible for generating code based on task specifications."""

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the developer agent."""
        self.model_name = model_name

    def generate_code(self, task_spec: TaskSpec) -> GeneratedArtifact:
        """Generate code based on the task specification."""
        # Placeholder for AI-based code generation
        code = f'''"""
Generated code for: {task_spec.description}
"""

def main():
    """Main function."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
        return GeneratedArtifact(
            content=code,
            file_type="py",
            agent_name="developer",
            metadata={"task_description": task_spec.description},
        )

    def refine_code(
        self, artifact: GeneratedArtifact, feedback: str
    ) -> GeneratedArtifact:
        """Refine code based on feedback."""
        # Placeholder for code refinement
        refined_content = artifact.content + f"\n# Refined based on: {feedback}"
        return GeneratedArtifact(
            content=refined_content,
            file_type=artifact.file_type,
            agent_name="developer",
            metadata=artifact.metadata,
        )

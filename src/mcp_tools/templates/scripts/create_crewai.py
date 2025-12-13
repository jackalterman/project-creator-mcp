
import os
import argparse

def create_crewai_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("crewai\nlangchain_openai\n")

    # agents.py
    agents_py_content = """from crewai import Agent
from langchain_openai import ChatOpenAI

# You can use any LLM here. Defaults to OpenAI GPT-4.
# Make sure to set OPENAI_API_KEY in your environment.
llm = ChatOpenAI(model="gpt-4")

class ProjectAgents:
    def researcher(self):
        return Agent(
            role='Senior Researcher',
            goal='Uncover groundbreaking technologies',
            backstory='Driven by curiosity, you explore the depths of the internet to find the latest tech.',
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def writer(self):
        return Agent(
            role='Tech Content Strategist',
            goal='Craft compelling content on tech advancements',
            backstory='You are a renowned Content Strategist, known for your insightful and engaging articles.',
            verbose=True,
            allow_delegation=True,
            llm=llm
        )
"""
    with open(os.path.join(project_path, "agents.py"), "w") as f:
        f.write(agents_py_content)

    # tasks.py
    tasks_py_content = """from crewai import Task

class ProjectTasks:
    def research_task(self, agent, topic):
        return Task(
            description=f"Conduct a comprehensive analysis of {topic}.",
            expected_output="A detailed report summarizing key findings.",
            agent=agent
        )

    def write_task(self, agent, context):
        return Task(
            description="Write a blog post based on the research findings.",
            expected_output="A formatted blog post ready for publication.",
            agent=agent,
            context=[context] # Pass the output of the research task
        )
"""
    with open(os.path.join(project_path, "tasks.py"), "w") as f:
        f.write(tasks_py_content)

    # main.py
    main_py_content = """import os
from crewai import Crew, Process
from agents import ProjectAgents
from tasks import ProjectTasks

# Check for API Key
if "OPENAI_API_KEY" not in os.environ:
    print("WARNING: OPENAI_API_KEY is not set. The agents might fail to run.")

def run():
    agents = ProjectAgents()
    tasks = ProjectTasks()

    # Instantiate Agents
    researcher = agents.researcher()
    writer = agents.writer()

    # Instantiate Tasks
    topic = "The future of AI Agents"
    task1 = tasks.research_task(researcher, topic)
    task2 = tasks.write_task(writer, task1)

    # Form the Crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        process=Process.sequential,
        verbose=True
    )

    # Kickoff
    result = crew.kickoff()
    print("######################")
    print(result)

if __name__ == "__main__":
    run()
"""
    with open(os.path.join(project_path, "main.py"), "w") as f:
        f.write(main_py_content)

    print(f"CrewAI project '{project_name}' created at {project_path}")
    print("Don't forget to set your OPENAI_API_KEY before running!")
    print("Run 'python main.py' to start the crew.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a CrewAI project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_crewai_project(args.project_name, args.target_dir)

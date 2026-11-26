# Generating train and test data for the system 

- to generate traces, two main agentic systems would be used 
1. A2A finance agentic financial system that has multiple agents that communicate through the Google A2A protocol to achieve a given financial task. These tasks could be ranged from accounting, data analytics, and tax technology.

Eval - this agent should complete complex taks that involves heavy computations and smart decision making to 
reach a goal. A gold set of evaluation tests will be run comparing the agent outputs in terms of accuracy, quality, and expected output format. 

After evaluations, any degraded, poor, or incorrect traces will be use to train and test the agentTace system.
These include:
- Failing test cases in terms of accuracy 
- unstructured outputs: expected JSON or a singe int, but the agent added unncessary texts with the expected result.
- results without expected work or hallucinated outputs 

2. A SRE agentic system that examines codebases and given logs/signals for an application failure and correct the issue/restore the service. Use multi agent architecture with A2A communication between the agents 

Setup - sample codebases and logs will be used for testing the agentic system. These include codebases from multi complexities, deployment failures, and triggering redeployments, etc.

Eval - agent's actions will be evaluated aganist a gold set and any code generated or any missed steps in the recovery process will mark a trace as an unsuccessful agent execution.

After evaluations, any degraded, poor, or incorrect traces will be use to train and test the agentTace system.
These include:
- incorrect PRs/fixes
- unneccessary code changes
- failed test cases and remaining issues.

NOTE FOR BOTH AGENTS: THE AGENTS SHOULD HAVE NECESSARY TOOLS, MCPS, RESOURCES, PROMPTS, AND EXTERNAL RESOURCES AS NEEDED. THESE INCLUDE MOCK OR TEST FINANCIAL DATA FILES, DATABASES, EXTERNAL APIS FOR THE FINANCE SYSTEM. AND FOR THE SRE AGENT, THESE INCLUDE READING FILES, WRITING TO FILES, EXECUTING BASH COMMANDS, GIT TOOLS, ETC. AGENTS HAVE TO COMPLEX ENOUGH FOR OBSERVING FAILURES

# Tech stack 

- for generating test data, agents, and traces open-source, free tired provides, and free APIs should be used. These include groq, gemini(free with an API key until a certain limit). 

- All the gold sets should be testable deterministically

A2A code references: https://codelabs.developers.google.com/intro-a2a-purchasing-concierge#11

# Intended workflow 

- build the two a2a systems 
- seperately build the gold set for each system with exact prompt and the output that could be evaluated deterministically
- run the agentic workflows in the gold set and collect the results 
- send all the failed workflows to the data collector (kafka)
- then build the system on top of them as training data 
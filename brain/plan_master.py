from __future__ import annotations
import json
import os
import yaml
from brain.planning import request_plan, extract_first_json_object
from brain.ollama_client import chat

def create_master_plan(max_retries: int = 5) -> bool:
    plan_path = os.path.join("configs", "master_plan.json")

    if os.path.exists(plan_path):
        print("[MASTER] Plano Mestre já existe.")
        return True

    os.makedirs("configs", exist_ok=True)

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Prompt ultra-detalhado para garantir que o código C# é funcional e "blindado"
    goal = (
        "Create a Unity project called game_001. "
        "1) Find Unity Editor. 2) Create project. 3) Create Assets/Editor, Builds, Scenes. "
        "4) Write: BuildScript.cs (Bake NavMesh, Tags), GameManager.cs (Metrics Export, Genome Load), "
        "ChaserAI.cs (OnTriggerEnter death), SimpleAgent.cs (NavMesh Agent). "
        "5) Execute BuildScript.MakeBuild."
    )

    print(f"[MASTER] Gerando Plano Mestre (Max {max_retries} tentativas)...")

    # Usamos o request_plan original para manter a compatibilidade com o teu sistema de planeamento
    # Aqui simulamos os objetos necessários para o request_plan funcionar
    system_prompt = "You are a Unity Automation Expert. Output ONLY JSON."
    planner_obj = {"schema": {}, "constraints": {"allowed_tools": ["find_unity_editor", "unity_create_project", "run_cmd", "write_file", "unity_run_execute_method"]}}
    env_data = {"os": "Windows"}

    for attempt in range(max_retries):
        # Nota: Adaptamos a chamada para a tua estrutura de planning.py
        from brain.planning import request_plan
        plan, raw = request_plan(
            config=config,
            system_prompt=system_prompt,
            planner_obj=planner_obj,
            env_data=env_data,
            goal=goal,
            log_jsonl=lambda x, y: None,
            log_path="logs/master_gen.jsonl"
        )

        if plan and "steps" in plan:
            # Validação simples: o plano deve conter os scripts fundamentais
            plan_str = json.dumps(plan)
            if all(x in plan_str for x in ["BuildScript.cs", "GameManager.cs", "ChaserAI.cs"]):
                with open(plan_path, "w", encoding="utf-8") as f:
                    json.dump(plan, f, indent=2)
                print("[MASTER] Plano Mestre criado e validado.")
                return True

        print(f"[MASTER] Tentativa {attempt+1} falhou. Re-tentando...")

    return False
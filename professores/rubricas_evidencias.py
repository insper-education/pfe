"""Fluxo adaptativo de evidências usado na avaliação de bancas."""

import hashlib
import json
import os

from django.conf import settings

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


CONFIG_DIR = "preenchimento-rubrica-evidencias-intermediaria"
RUBRIC_FILES = {
    "execucao-tecnica": "wizard-evidencias-sim-nao.yaml",
    "execucao_tecnica": "wizard-evidencias-sim-nao.yaml",
}
VALID_NODE_TYPES = {"single_choice", "review"}


class RubricConfigError(Exception):
    """Configuração do wizard inválida."""


def rubric_slug_to_id(slug):
    return slug.replace("-", "_")


def rubric_id_to_slug(rubric_id):
    return rubric_id.replace("_", "-")


def _config_path(rubric_slug):
    try:
        filename = RUBRIC_FILES[rubric_slug]
    except KeyError:
        raise RubricConfigError("Rubrica de evidências não encontrada: {0}".format(rubric_slug))
    return os.path.join(settings.BASE_DIR, CONFIG_DIR, filename)


def load_rubric_config(rubric_slug):
    if yaml is None:
        raise RubricConfigError("PyYAML não está instalado.")
    path = _config_path(rubric_slug)
    try:
        with open(path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
    except OSError as error:
        raise RubricConfigError("Não foi possível ler a configuração: {0}".format(error))
    if not isinstance(config, dict):
        raise RubricConfigError("O arquivo precisa conter um objeto YAML.")
    validate_rubric_config(config)
    with open(path, "rb") as config_file:
        config["_config_hash"] = hashlib.sha256(config_file.read()).hexdigest()
    return config


def validate_rubric_config(config):
    rubric = config.get("rubric") or {}
    if not config.get("schema_version") or not rubric.get("id"):
        raise RubricConfigError("schema_version e rubric.id são obrigatórios.")
    if rubric.get("presentation") != "conditional_boolean":
        raise RubricConfigError("A apresentação deve ser conditional_boolean.")
    nodes = rubric.get("nodes") or []
    by_id = {node.get("id"): node for node in nodes}
    if not nodes or len(by_id) != len(nodes) or None in by_id:
        raise RubricConfigError("Cada pergunta precisa ter um id único.")
    if rubric.get("start_node") not in by_id:
        raise RubricConfigError("start_node não encontrado.")
    valid_grades = {grade.get("id") for grade in rubric.get("scale") or []}
    for node in nodes:
        if node.get("type") not in VALID_NODE_TYPES:
            raise RubricConfigError("Tipo de pergunta inválido: {0}".format(node.get("id")))
        if node.get("type") == "review":
            continue
        options = node.get("options") or []
        if len(options) != 2 or {option.get("id") for option in options} != {"sim", "nao"}:
            raise RubricConfigError("A pergunta {0} deve ter Sim e Não.".format(node.get("id")))
        for option in options:
            target = option.get("next") or node.get("next")
            if target and target not in by_id:
                raise RubricConfigError("Próxima pergunta inválida em {0}.".format(node.get("id")))
            if option.get("maximum_grade") and option["maximum_grade"] not in valid_grades:
                raise RubricConfigError("Limite inválido em {0}.".format(node.get("id")))


def get_nodes(config):
    return {node["id"]: node for node in config["rubric"]["nodes"]}


def get_option(node, option_id):
    return next((option for option in node.get("options", []) if option["id"] == option_id), None)


def next_node_id(node, answers):
    if node.get("type") == "review":
        return None
    selected = (answers.get(node["id"]) or [None])[0]
    option = get_option(node, selected)
    return (option or {}).get("next") or node.get("next")


def calculate_path(config, answers):
    nodes = get_nodes(config)
    current_id, path, visited = config["rubric"]["start_node"], [], set()
    while current_id:
        if current_id in visited:
            raise RubricConfigError("Ciclo detectado em {0}.".format(current_id))
        visited.add(current_id)
        path.append(current_id)
        node = nodes[current_id]
        if node.get("type") == "review" or (node.get("required") and not answers.get(current_id)):
            break
        current_id = next_node_id(node, answers)
    return path


def prune_answers_to_path(config, answers):
    valid_path = set(calculate_path(config, answers))
    return {node_id: value for node_id, value in answers.items() if node_id in valid_path}


def update_answer(config, answers, node_id, selected_ids):
    option_id = (selected_ids or [None])[0]
    node = get_nodes(config)[node_id]
    if not get_option(node, option_id):
        return answers
    updated = dict(answers)
    updated[node_id] = [option_id]
    return prune_answers_to_path(config, updated)


def is_node_answer_valid(node, selected_ids):
    return node.get("type") == "review" or not node.get("required") or len(selected_ids) == 1


def collect_answer_details(config, answers):
    nodes = get_nodes(config)
    details = []
    for node_id in calculate_path(config, answers):
        node = nodes[node_id]
        option = get_option(node, (answers.get(node_id) or [None])[0])
        if option:
            details.append({"node": node, "options": [option]})
    return details


def calculate_maximum_grade(config, answers):
    grades = {item["id"]: float(item["rank"]) for item in config["rubric"]["scale"]}
    limits = [option["maximum_grade"] for detail in collect_answer_details(config, answers)
              for option in detail["options"] if option.get("maximum_grade")]
    return min(limits, key=lambda grade: grades[grade]) if limits else config["rubric"]["scale"][0]["id"]


def calculate_maximum_grades(config, answers):
    result = {}
    for detail in collect_answer_details(config, answers):
        objective, option = detail["node"].get("objective"), detail["options"][0]
        if objective and option.get("maximum_grade"):
            result[objective] = option["maximum_grade"]
    return result


def calculate_rubric_recommendation(config, answers):
    """Compatibilidade temporária para registros legados sem sugestão de nota."""
    return {
        "recommendedGrade": "I",
        "dimensionResults": [],
        "appliedCaps": [],
        "warnings": [],
        "rationale": [],
        "nextGradeRequirements": [],
    }


def rubric_state_to_json(data):
    return json.dumps(data or {}, ensure_ascii=False, sort_keys=True)


def rubric_state_from_json(data, default=None):
    if not data:
        return {} if default is None else default
    return json.loads(data)

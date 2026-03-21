from __future__ import annotations


def build_wrapper_rcfile() -> str:
    return r"""# cyber-shell rcfile
if [[ -f /etc/bash.bashrc ]]; then
  source /etc/bash.bashrc
fi

if [[ -f ~/.bashrc ]]; then
  source ~/.bashrc
fi

export HISTCONTROL=
export HISTIGNORE=
shopt -s cmdhist lithist

__cyber_shell_write_control() {
  [[ -n "${CYBER_SHELL_CONTROL_FD:-}" ]] || return 0
  printf '%s\0' "$@" >&${CYBER_SHELL_CONTROL_FD}
}

__cyber_shell_now() {
  local __cyber_shell_now_value
  printf -v __cyber_shell_now_value '%(%Y-%m-%dT%H:%M:%SZ)T' -1
  printf '%s' "${__cyber_shell_now_value}"
}

__cyber_shell_preexec() {
  local started_at
  started_at="$(__cyber_shell_now)"
  __cyber_shell_write_control PRE "${started_at}"
}

__cyber_shell_last_command() {
  builtin fc -ln -1
}

__cyber_shell_postexec() {
  local exit_code finished_at last_cmd
  exit_code=$?
  finished_at="$(__cyber_shell_now)"
  last_cmd="$(__cyber_shell_last_command)"
  __cyber_shell_write_control POST "${finished_at}" "${exit_code}" "${PWD}" "${last_cmd}"
  return "${exit_code}"
}

__cyber_shell_append_prompt_command() {
  if declare -p PROMPT_COMMAND >/dev/null 2>&1; then
    if declare -p PROMPT_COMMAND 2>/dev/null | grep -q 'declare \-a'; then
      PROMPT_COMMAND=("__cyber_shell_postexec" "${PROMPT_COMMAND[@]}")
    elif [[ -n "${PROMPT_COMMAND}" ]]; then
      PROMPT_COMMAND="__cyber_shell_postexec;${PROMPT_COMMAND}"
    else
      PROMPT_COMMAND="__cyber_shell_postexec"
    fi
  else
    PROMPT_COMMAND="__cyber_shell_postexec"
  fi
}

__cyber_shell_append_prompt_command
PS0='$(__cyber_shell_preexec)'${PS0:-}
"""

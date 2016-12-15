# bash completion for preupgrade-assistant
_preupg_scan() {
    echo $(cd /usr/share/preupgrade; ls -d *)
}

_preupg_result(){
    echo $(cd /root/preupgrade-results; ls -1 *.tar.gz)
}

_preupg() {
    # read output and returncode of the command with "-h"
    local opts cur prev comps
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-s --scan -v --verbose -d --debug --skip-common -u --upload -r --results --list-contents-set -c --contents
     -a --apply --riskcheck --force --text -m --mode --cleanup --select-rules --list-rules"

    #echo "SS${COMP_CWORD} and ${COMP_WORDS} and ${prev} and ${cur}SS"
    if [[ ${COMP_CWORD} == 1 && ${COMP_WORDS} == "preupg" ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${COMP_CWORD} == 1 && ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    comps=""
    case "${prev}" in
        "-s"|"--scan")
        comps=$(_preupg_scan)
        ;;
        "-u"|"--upload")
        comps="http://127.0.0.1:8099/submit/"
        ;;
        "-r"|"--results")
        comps=$(_preupg_result)
        ;;
        "--riskcheck")
        opts="-v --verbose -d --debug"
        comps="$opts"
        ;;
        *)
        prev="${COMP_WORDS[COMP_CWORD-2]}"
        case "${prev}" in
            "-s"|"--scan")
            opts="-v --verbose -d --debug --skip-common --riskcheck --force --text"
            comps="$opts"
            ;;
            "-u"|"--upload")
            opts="-v --verbose -d --debug -r --results"
            comps="$opts"
            ;;
            "-r"|"--results")
            opts="-v --verbose -d --debug -u --upload"
            comps="$opts"
            ;;
            *)
            result=$( compgen -A file -- "$cur" )
            compopt -o filenames
            ;;
        esac
        #echo "$opts and $comps"
        COMPREPLY=( $(compgen -W "${comps}" -- "${cur}" ) )
        ;;
    esac

    COMPREPLY=( $(compgen -W "${comps}" -- "${cur}" ) )
    return 0

}
complete -F _preupg -o filenames preupg
# Local variables:
# mode: shell-script
# sh-basic-offset: 4
# sh-indent-comment: t
# indent-tabs-mode: nil
# End:
# ex: ts=4 sw=4 et filetype=sh

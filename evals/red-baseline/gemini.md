Gemini CLI /init run FAILED before producing GEMINI.md.

Command: cd $SCR/gemini && timeout 600 gemini -p "/init" --yolo
Exit code: 55
Wall time: 3s

Last lines of gemini.log:
}
YOLO mode is enabled. All tool calls will be automatically approved.
Approval mode overridden to "default" because the current folder is not trusted.
Gemini CLI is not running in a trusted directory. To proceed, either use `--skip-trust`, set the `GEMINI_CLI_TRUST_WORKSPACE=true` environment variable, or trust this directory in interactive mode. For more details, see https://geminicli.com/docs/cli/trusted-folders/#headless-and-automated-environments

Root cause (confirmed by a separate retry with --skip-trust added): an account-eligibility failure, not a flag/config issue.
Error authenticating: IneligibleTierError: This client is no longer supported for Gemini Code Assist for individuals. To continue using Gemini, please migrate to the Antigravity suite of products: https://antigravity.google

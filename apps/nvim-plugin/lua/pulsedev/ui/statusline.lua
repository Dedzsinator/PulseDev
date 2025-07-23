local M = {}

function M.statusline()
  local g = vim.g.pulsedev_gamification or {}
  local status = g.status or 'UNKNOWN'
  local color = status == 'ACTIVE' and '%#StatusLine#' or '%#StatusLineError#'
  return string.format('%s[PulseDev: %s | L%d | XP:%d | 🔥%d]', color, status, g.level or 0, g.xp or 0, g.streak or 0)
end

return M

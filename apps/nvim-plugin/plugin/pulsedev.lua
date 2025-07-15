-- plugin/pulsedev.lua
-- Entry point for PulseDev Neovim plugin

if vim.g.loaded_pulsedev == 1 then
  return
end

vim.g.loaded_pulsedev = 1

-- Only load if Neovim version is supported
if vim.fn.has('nvim-0.8') == 0 then
  vim.notify('PulseDev requires Neovim 0.8 or higher', vim.log.levels.ERROR)
  return
end

-- Load the main module
require('pulsedev').setup()
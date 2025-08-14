-- PulseDev+ Neovim Plugin Configuration for lazy.nvim
-- Save this as: ~/.config/nvim/lua/plugins/pulsedev.lua

return {
  {
    "PulseDev+",
    -- Use the local plugin directory
    dir = vim.fn.expand("~/Documents/Programming/PulseDev/apps/nvim-plugin"), -- Update this path!
    name = "pulsedev",

    -- Plugin configuration
    config = function()
      require("pulsedev").setup({
        -- Core settings
        enabled = true,
        debug = true, -- Enable for testing and troubleshooting

        -- Backend API connection
        api = {
          endpoint = "http://localhost:8000",
          timeout = 30,
          retry_count = 3,
        },

        -- Redis connection (optional)
        redis = {
          host = "localhost",
          port = 6379,
          password = nil,
        },

        -- Context tracking features
        context = {
          track_cursor = true,
          track_buffers = true,
          track_activity = true,
          track_flow = true,
          cursor_throttle = 2000,
          activity_timeout = 60000,
        },

        -- Auto-commit features
        auto_commit = {
          enabled = true,
          on_test_pass = true,
          on_stable_context = true,
          message_template = "PulseDev: {action} | {context}",
        },

        -- Flow state detection
        flow = {
          enabled = true,
          keystroke_threshold = 5,
          idle_threshold = 30,
        },

        -- Gamification features
        gamification = {
          enabled = true,
          show_level = true,
          show_xp = true,
          show_achievements = true,
          notifications = true,
        },

        -- UI settings
        ui = {
          show_status = true,
          show_metrics = true,
          update_interval = 5000,
        },
      })

      -- Optional: Set up keymaps
      local keymap = vim.keymap.set
      keymap("n", "<leader>pd", ":PulseDev dashboard<CR>", { desc = "PulseDev Dashboard" })
      keymap("n", "<leader>ps", ":PulseDev status<CR>", { desc = "PulseDev Status" })
      keymap("n", "<leader>pm", ":PulseDev metrics<CR>", { desc = "PulseDev Metrics" })
      keymap("n", "<leader>pf", ":PulseDev flow<CR>", { desc = "PulseDev Flow State" })
    end,

    -- Dependencies
    dependencies = {
      "nvim-lua/plenary.nvim", -- Required for HTTP requests and utilities
    },

    -- Load on Neovim start
    event = "VimEnter",

    -- Optional: Add commands that should be available immediately
    cmd = {
      "PulseDev",
    },
  }
}

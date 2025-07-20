describe('API Integration Tests', () => {
  beforeEach(() => {
    cy.visit('/dashboard')
  })

  it('submits context events successfully', () => {
    cy.intercept('POST', '/api/v1/context/events', {
      statusCode: 200,
      body: { status: 'success', event_id: 'test-event-123' }
    }).as('submitContextEvent')

    cy.contains('Events').click()
    
    cy.get('[data-testid="context-event-form"]').within(() => {
      cy.get('select[name="agent"]').select('vscode')
      cy.get('select[name="type"]').select('file_edit')
      cy.get('textarea[name="payload"]').type('{"file": "test.ts", "action": "edit"}')
      cy.get('button[type="submit"]').click()
    })

    cy.wait('@submitContextEvent').then((interception) => {
      expect(interception.request.body).to.have.property('agent', 'vscode')
      expect(interception.request.body).to.have.property('type', 'file_edit')
    })

    cy.contains('Event submitted successfully')
  })

  it('handles context event submission errors', () => {
    cy.intercept('POST', '/api/v1/context/events', {
      statusCode: 500,
      body: { error: 'Internal Server Error' }
    }).as('submitContextEventError')

    cy.contains('Events').click()
    
    cy.get('[data-testid="context-event-form"]').within(() => {
      cy.get('select[name="agent"]').select('browser')
      cy.get('select[name="type"]').select('tab_switch')
      cy.get('textarea[name="payload"]').type('{"url": "test.com"}')
      cy.get('button[type="submit"]').click()
    })

    cy.wait('@submitContextEventError')
    cy.contains('Error submitting event')
  })

  it('loads gamification data with proper API calls', () => {
    cy.intercept('GET', '/api/v1/gamification/dashboard/*', {
      delay: 1000, // Simulate slow network
      statusCode: 200,
      body: { success: true, dashboard: { user_stats: {}, achievements: [], leaderboards: {} } }
    }).as('slowGamificationLoad')

    cy.contains('Gamification').click()
    
    // Should show loading state
    cy.contains('Loading gamification data')
    
    cy.wait('@slowGamificationLoad')
    
    // Should show content after loading
    cy.contains('Gamification Dashboard')
  })

  it('handles network failures gracefully', () => {
    cy.intercept('GET', '/api/v1/gamification/dashboard/*', { forceNetworkError: true }).as('networkError')

    cy.contains('Gamification').click()
    cy.wait('@networkError')
    
    cy.contains('Error loading gamification data')
  })

  it('retries failed requests', () => {
    let callCount = 0
    cy.intercept('GET', '/api/v1/gamification/dashboard/*', (req) => {
      callCount++
      if (callCount === 1) {
        req.reply({ statusCode: 500 })
      } else {
        req.reply({ 
          statusCode: 200, 
          body: { success: true, dashboard: { user_stats: {}, achievements: [], leaderboards: {} } }
        })
      }
    }).as('retryRequest')

    cy.contains('Gamification').click()
    
    // Should eventually succeed after retry
    cy.contains('Gamification Dashboard', { timeout: 10000 })
  })

  it('validates API response structure', () => {
    cy.intercept('GET', '/api/v1/gamification/dashboard/*', (req) => {
      req.reply({
        statusCode: 200,
        body: {
          success: true,
          dashboard: {
            user_stats: {
              id: 'test-user',
              username: 'testuser',
              total_xp: 1000,
              level: 5,
              current_streak: 7,
              longest_streak: 15,
              total_commits: 42,
              total_flow_time: 300
            },
            achievements: [],
            leaderboards: { xp: [], streaks: [] }
          }
        }
      })
    }).as('validApiResponse')

    cy.contains('Gamification').click()
    cy.wait('@validApiResponse')
    
    // Should render the data correctly
    cy.contains('Level 5')
    cy.contains('1,000 XP')
    cy.contains('7 days')
  })
})
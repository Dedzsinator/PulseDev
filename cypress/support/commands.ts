/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to simulate gamification data loading
       */
      interceptGamificationAPI(): Chainable<void>
      
      /**
       * Custom command to navigate to dashboard
       */
      visitDashboard(): Chainable<void>
      
      /**
       * Custom command to submit context event
       */
      submitContextEvent(eventData: any): Chainable<void>
    }
  }
}

Cypress.Commands.add('interceptGamificationAPI', () => {
  cy.intercept('GET', '/api/v1/gamification/dashboard/*', {
    fixture: 'gamification-dashboard.json'
  }).as('getDashboard')
  
  cy.intercept('POST', '/api/v1/gamification/xp/award', {
    statusCode: 200,
    body: { success: true, xp_earned: 100 }
  }).as('awardXP')
  
  cy.intercept('GET', '/api/v1/gamification/leaderboard*', {
    fixture: 'leaderboard.json'
  }).as('getLeaderboard')
})

Cypress.Commands.add('visitDashboard', () => {
  cy.visit('/dashboard')
})

Cypress.Commands.add('submitContextEvent', (eventData) => {
  cy.intercept('POST', '/api/v1/context/events', {
    statusCode: 200,
    body: { status: 'success', event_id: 'test-123' }
  }).as('submitEvent')
  
  cy.get('[data-testid="context-event-form"]').within(() => {
    cy.get('select[name="agent"]').select(eventData.agent)
    cy.get('select[name="type"]').select(eventData.type)
    cy.get('textarea[name="payload"]').type(JSON.stringify(eventData.payload))
    cy.get('button[type="submit"]').click()
  })
  
  cy.wait('@submitEvent')
})
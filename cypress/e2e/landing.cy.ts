describe('Landing Page', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('displays the main hero section', () => {
    cy.get('h1').should('contain', 'PulseDev+')
    cy.get('h2').should('contain', 'Your AI-Powered Development Companion')
    cy.contains('Experience the future of development')
  })

  it('shows all feature sections', () => {
    // Core features
    cy.contains('Cognitive Context Mirror')
    cy.contains('Auto-Commit Intelligence')
    cy.contains('Flow State Detection')
    cy.contains('Unified Gamification')
    
    // Platform integrations
    cy.contains('Multi-Platform Integration')
    cy.contains('VS Code Extension')
    cy.contains('Browser Extension')
    cy.contains('Neovim Plugin')
  })

  it('has working call-to-action buttons', () => {
    cy.contains('Get Started Today').should('be.visible')
    cy.contains('Launch Dashboard').should('be.visible').click()
    
    // Should navigate to dashboard
    cy.url().should('include', '/dashboard')
  })

  it('displays all feature cards with icons', () => {
    // Should have multiple feature cards
    cy.get('[data-testid="feature-card"]').should('have.length.greaterThan', 8)
    
    // Each feature card should have an icon (SVG)
    cy.get('[data-testid="feature-card"] svg').should('have.length.greaterThan', 8)
  })

  it('is responsive on mobile devices', () => {
    cy.viewport('iphone-x')
    
    cy.get('h1').should('be.visible')
    cy.contains('Launch Dashboard').should('be.visible')
    
    // Feature cards should stack on mobile
    cy.get('[data-testid="feature-card"]').first().should('be.visible')
  })

  it('has proper navigation structure', () => {
    // Should have proper heading hierarchy
    cy.get('h1').should('have.length', 1)
    cy.get('h2').should('have.length.greaterThan', 3)
    
    // Footer should be present
    cy.contains('© 2024 PulseDev+')
  })
})
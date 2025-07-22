describe('PulseDev+ Tauri App', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('shows the dashboard and tabs', () => {
    cy.contains('PulseDev+ Cognitive Context Mirror');
    cy.contains('CCM');
    cy.contains('AI Prompt');
    cy.contains('Auto Commit');
    cy.contains('Flow');
    cy.contains('Energy');
    cy.contains('Code Map');
    cy.contains('Git Monitor');
    cy.contains('Integrations');
    cy.contains('Merge Resolver');
    cy.contains('Intent Drift');
    cy.contains('Branch Suggest');
    cy.contains('Native Utilities');
  });

  it('can open Native Utilities and see actions', () => {
    cy.contains('Native Utilities').click();
    cy.contains('Pick File').should('exist');
    cy.contains('Pick and Read File').should('exist');
    cy.contains('Pick and Write File').should('exist');
    cy.contains('Get DND Status').should('exist');
    cy.contains('Enable DND (Mock)').should('exist');
    cy.contains('Disable DND (Mock)').should('exist');
  });

  it('can open Merge Resolver and see input', () => {
    cy.contains('Merge Resolver').click();
    cy.get('input[placeholder="/path/to/your/repo"]').should('exist');
    cy.contains('Scan for Merge Conflicts').should('exist');
  });

  it('can open Intent Drift and see input', () => {
    cy.contains('Intent Drift').click();
    cy.get('input[placeholder="Describe your original intent/task"]').should('exist');
    cy.contains('Check for Intent Drift').should('exist');
  });

  it('can open Branch Suggest and see button', () => {
    cy.contains('Branch Suggest').click();
    cy.contains('Suggest Branch Name').should('exist');
  });
}); 
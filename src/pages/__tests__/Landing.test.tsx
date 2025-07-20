import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import Landing from '../Landing'

describe('Landing Page', () => {
  it('renders main hero section', () => {
    render(<Landing />)
    
    expect(screen.getByText('PulseDev+')).toBeInTheDocument()
    expect(screen.getByText(/Your AI-Powered Development Companion/)).toBeInTheDocument()
    expect(screen.getByText(/Experience the future of development/)).toBeInTheDocument()
  })

  it('renders all feature sections', () => {
    render(<Landing />)
    
    // Core features
    expect(screen.getByText('Cognitive Context Mirror')).toBeInTheDocument()
    expect(screen.getByText('Auto-Commit Intelligence')).toBeInTheDocument()
    expect(screen.getByText('Flow State Detection')).toBeInTheDocument()
    expect(screen.getByText('Unified Gamification')).toBeInTheDocument()
    
    // Platform integrations
    expect(screen.getByText('Multi-Platform Integration')).toBeInTheDocument()
    expect(screen.getByText('VS Code Extension')).toBeInTheDocument()
    expect(screen.getByText('Browser Extension')).toBeInTheDocument()
    expect(screen.getByText('Neovim Plugin')).toBeInTheDocument()
  })

  it('renders security and enterprise features', () => {
    render(<Landing />)
    
    expect(screen.getByText('Enterprise Security')).toBeInTheDocument()
    expect(screen.getByText('AES-256-GCM encryption')).toBeInTheDocument()
    expect(screen.getByText('Enterprise Analytics')).toBeInTheDocument()
    expect(screen.getByText('Developer Tools')).toBeInTheDocument()
  })

  it('renders call-to-action buttons', () => {
    render(<Landing />)
    
    expect(screen.getByText('Get Started Today')).toBeInTheDocument()
    expect(screen.getByText('Launch Dashboard')).toBeInTheDocument()
  })

  it('renders footer with copyright', () => {
    render(<Landing />)
    
    expect(screen.getByText(/© 2024 PulseDev\+/)).toBeInTheDocument()
    expect(screen.getByText(/Built with love by developers, for developers/)).toBeInTheDocument()
  })

  it('has proper heading hierarchy', () => {
    render(<Landing />)
    
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1).toHaveTextContent('PulseDev+')
    
    const h2Elements = screen.getAllByRole('heading', { level: 2 })
    expect(h2Elements.length).toBeGreaterThan(0)
  })

  it('renders feature icons', () => {
    render(<Landing />)
    
    // Check that SVG icons are present (Lucide icons render as SVGs)
    const svgElements = document.querySelectorAll('svg')
    expect(svgElements.length).toBeGreaterThan(10) // Should have many icons
  })
})
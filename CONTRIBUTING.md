# Contributing to Spatial-RAG

Thank you for your interest in contributing to Spatial-RAG! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/Spatial-RAG.git
   cd Spatial-RAG
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/originalowner/Spatial-RAG.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

Follow the [README.md](README.md) Quick Start guide to set up your development environment.

## Code Style

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where possible
- Maximum line length: 100 characters
- Use `black` for formatting (if configured)
- Add docstrings to all functions and classes

Example:
```python
def retrieve_documents(
    query: str,
    center_lat: float,
    center_lon: float,
    radius_m: float = 1000.0
) -> list[Document]:
    """
    Retrieve documents using hybrid spatial-semantic search.
    
    Args:
        query: Natural language query string
        center_lat: Center latitude for spatial search
        center_lon: Center longitude for spatial search
        radius_m: Search radius in meters
        
    Returns:
        List of Document objects ranked by hybrid score
    """
    ...
```

### TypeScript/React (Frontend)

- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Prefer named exports
- Use meaningful variable and function names

Example:
```typescript
interface QueryResponse {
  query: string;
  answer: string | null;
  documents: Document[];
}

export function QueryPanel(): JSX.Element {
  const { query, setQuery } = useStore();
  // ...
}
```

## Commit Messages

Write clear, descriptive commit messages:

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Fix bug" not "Fixes bug")
- First line should be 50 characters or less
- Include more details in the body if needed

Examples:
```
Add polygon drawing support to map component

- Implement react-leaflet-draw integration
- Add GeoJSON to WKT conversion utility
- Update query endpoint to accept region_geojson parameter
```

## Pull Request Process

1. **Update your fork** with latest changes:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   git push origin main
   ```

2. **Create your feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub with:
   - Clear title and description
   - Reference any related issues
   - Include screenshots for UI changes
   - Ensure all tests pass (if applicable)

## Testing

Before submitting a PR:

- Test your changes locally
- Ensure the application builds successfully
- Test API endpoints with curl or Postman
- Verify frontend components render correctly
- Check for console errors/warnings

## Areas for Contribution

We welcome contributions in these areas:

- **New Features**: Additional retrieval strategies, UI improvements, new map features
- **Bug Fixes**: Fix issues reported in GitHub Issues
- **Documentation**: Improve README, add code comments, write tutorials
- **Performance**: Optimize queries, improve embedding caching, reduce latency
- **Testing**: Add unit tests, integration tests, E2E tests
- **Accessibility**: Improve UI accessibility, keyboard navigation

## Questions?

Feel free to open an issue on GitHub for questions or discussions about contributions.

Thank you for contributing to Spatial-RAG! 🎉


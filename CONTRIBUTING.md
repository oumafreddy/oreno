# Contributing to Oreno GRC

Thank you for your interest in contributing to Oreno GRC! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (recommended) or SQLite
- Git

**Optional:**
- Node.js 18+ (for frontend assets)
- Docker (for containerized development)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/oumafreddy/oreno.git
   cd oreno
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Environment Configuration**
   ```bash
   cp env.example .env.oreno
   # Edit .env.oreno with your configuration
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate --settings=config.settings.development
   python manage.py createsuperuser --settings=config.settings.development
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver --settings=config.settings.development
   ```

## 📋 Contribution Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use Black for code formatting
- Use isort for import sorting
- Follow Django best practices
- Write meaningful commit messages

### Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write tests for new functionality
   - Update documentation if needed
   - Ensure all tests pass

3. **Test Your Changes**
   ```bash
   python manage.py test --settings=config.settings.development
   ```

4. **Submit Pull Request**
   - Provide a clear description
   - Reference any related issues
   - Include screenshots for UI changes

### Issue Reporting

When reporting issues, please include:
- Python version
- Django version
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)

## 🏗️ Project Structure

```
oreno/
├── apps/                    # Django applications
│   ├── audit/              # Audit management
│   ├── risk/               # Risk management
│   ├── compliance/         # Compliance tracking
│   ├── contracts/          # Contract management
│   ├── ai_governance/      # AI governance features
│   └── ...
├── config/                 # Django configuration
├── services/               # External service integrations
├── templates/              # HTML templates
├── static/                 # Static assets
└── tests/                  # Test suites
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test --settings=config.settings.development

# Run specific app tests
python manage.py test apps.audit --settings=config.settings.development

# Run with coverage
coverage run --source='.' manage.py test --settings=config.settings.development
coverage report
```

### Writing Tests
- Write unit tests for new models and views
- Include integration tests for complex workflows
- Test both success and failure scenarios
- Aim for >80% code coverage

## 📚 Documentation

### Code Documentation
- Use docstrings for all functions and classes
- Follow Google docstring format
- Document complex business logic
- Update README.md for significant changes

### API Documentation
- Document new API endpoints
- Include request/response examples
- Update OpenAPI/Swagger documentation

## 🔒 Security

### Security Guidelines
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Follow OWASP guidelines
- Report security issues privately to maintainers

### Security Reporting
For security vulnerabilities, please email: fredouma@oreno.tech or oumafredomondi@gmail.com

## 🏷️ Release Process

### Versioning
We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Release notes prepared

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different perspectives and approaches

### Communication Channels
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Pull Requests: Code contributions and reviews

## 🎯 Areas for Contribution

### High Priority
- [ ] Test coverage improvements
- [ ] Performance optimizations
- [ ] Documentation enhancements
- [ ] Security audit and improvements

### Feature Areas
- [ ] AI Governance enhancements
- [ ] Risk assessment tools
- [ ] Compliance automation
- [ ] Reporting improvements
- [ ] Mobile responsiveness

### Technical Debt
- [ ] Code refactoring
- [ ] Database optimization
- [ ] Frontend modernization
- [ ] API standardization

## 📞 Getting Help

- Check existing issues and discussions
- Join our community discussions
- Contact maintainers for guidance

## 🙏 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Community highlights

Thank you for contributing to Oreno GRC! 🎉

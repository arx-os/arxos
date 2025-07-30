# Getting Started with Arxos

## 🎯 **Welcome to Arxos**

Arxos is the world's most advanced building intelligence platform, combining CAD capabilities, AI-powered insights, and comprehensive building management tools. This guide will help you get started with your first building project.

**Estimated Time**: 15-20 minutes  
**Prerequisites**: None

---

## 🚀 **Quick Start**

### **Step 1: Access Arxos**

#### **Web Interface**
1. Open your browser and navigate to your Arxos instance
2. Click **"Get Started"** or **"Create Account"**
3. Complete the onboarding process

#### **Desktop Application (ArxIDE)**
1. Download ArxIDE from the Arxos website
2. Install and launch the application
3. Sign in with your Arxos account

#### **Command Line Interface**
```bash
# Install Arxos CLI
pip install arxos-cli

# Authenticate
arx auth login

# Verify installation
arx --version
```

### **Step 2: Create Your First Building**

#### **Using the Web Interface**
1. Click **"New Building"** from the dashboard
2. Enter building details:
   - **Name**: "My First Building"
   - **Type**: Commercial/Residential/Industrial
   - **Address**: Building location
3. Click **"Create Building"**

#### **Using ArxIDE**
1. Open ArxIDE
2. Click **"New Project"**
3. Select **"Building Project"**
4. Enter building information
5. Click **"Create Project"**

#### **Using CLI**
```bash
# Create a new building
arx building create "My First Building" --type commercial --address "123 Main St"

# List your buildings
arx building list

# View building details
arx building show "My First Building"
```

### **Step 3: Import or Create Building Data**

#### **Import Existing Data**
1. **SVG Files**: Drag and drop SVG files into the interface
2. **IFC Files**: Use the IFC import feature
3. **ASCII-BIM**: Import ASCII-BIM format files
4. **CAD Files**: Import DXF, DWG, or other CAD formats

#### **Create New Data**
1. **Draw Building**: Use the drawing tools to create building elements
2. **Add Components**: Insert HVAC, electrical, and plumbing components
3. **Define Systems**: Set up building systems and relationships

### **Step 4: Explore Building Intelligence**

#### **AI Agent Interaction**
1. Click the **AI Assistant** icon
2. Ask questions like:
   - "What systems are in this building?"
   - "Show me the HVAC layout"
   - "Generate a maintenance schedule"
3. Review AI-generated insights and recommendations

#### **System Analysis**
1. Navigate to **"Systems"** in the sidebar
2. Explore different building systems:
   - **HVAC**: Heating, ventilation, and air conditioning
   - **Electrical**: Power distribution and lighting
   - **Plumbing**: Water supply and drainage
   - **Fire Protection**: Safety systems
3. Click on systems to view detailed information

### **Step 5: Export and Share**

#### **Export Building Data**
1. Click **"Export"** in the top menu
2. Choose export format:
   - **IFC**: Industry Foundation Classes
   - **SVG**: Scalable Vector Graphics
   - **ASCII-BIM**: Text-based format
   - **PDF**: Documentation
3. Download your exported file

#### **Share with Team**
1. Click **"Share"** button
2. Enter email addresses
3. Set permissions (view/edit/admin)
4. Send invitation

---

## 📚 **Next Steps**

### **Learn the Basics**

#### **SVGX Format**
- Read the [SVGX Basics Tutorial](tutorials/svgx-basics.md)
- Learn about SVGX structure and syntax
- Practice creating simple SVGX files

#### **Command Line Interface**
- Complete the [CLI Basics Tutorial](tutorials/cli-basics.md)
- Learn essential commands
- Practice automation and scripting

#### **AI Agent**
- Explore the [AI Agent Guide](features/ai-agent-guide.md)
- Learn how to ask effective questions
- Discover AI-powered features

### **Advanced Features**

#### **Building Management**
- **Work Orders**: Create and manage maintenance tasks
- **Asset Tracking**: Monitor building components
- **Performance Analytics**: Track building performance
- **Predictive Maintenance**: AI-driven maintenance scheduling

#### **Integration**
- **CMMS Integration**: Connect to maintenance management systems
- **IoT Devices**: Integrate with building sensors
- **Third-Party Tools**: Connect to external systems
- **API Access**: Use Arxos APIs for custom integrations

---

## 🛠️ **Common Tasks**

### **View Building Information**
```bash
# List all buildings
arx building list

# Show building details
arx building show "Building Name"

# View building systems
arx building systems "Building Name"
```

### **Export Building Data**
```bash
# Export to IFC format
arx export ifc "Building Name" --output building.ifc

# Export to SVG format
arx export svg "Building Name" --output building.svg

# Export to ASCII-BIM format
arx export ascii-bim "Building Name" --output building.txt
```

### **Generate Reports**
```bash
# Generate building report
arx report generate "Building Name" --type building-overview

# Generate system report
arx report generate "Building Name" --type hvac-system

# Generate maintenance report
arx report generate "Building Name" --type maintenance-schedule
```

---

## ❓ **Getting Help**

### **Documentation**
- **User Guides**: Complete guides for all features
- **API Reference**: Technical documentation
- **Tutorials**: Step-by-step learning materials
- **Examples**: Code examples and use cases

### **Support Channels**
- **AI Assistant**: Ask questions directly in the interface
- **Community Forum**: Connect with other users
- **Email Support**: Contact support team
- **Video Tutorials**: Watch demonstration videos

### **Troubleshooting**
- **Common Issues**: [Troubleshooting Guide](troubleshooting/common-issues.md)
- **Debugging**: [Debugging Guide](troubleshooting/debugging.md)
- **FAQ**: [Frequently Asked Questions](troubleshooting/faq.md)

---

## 🎯 **Success Checklist**

### **Getting Started**
- [ ] Created Arxos account
- [ ] Accessed web interface or installed ArxIDE
- [ ] Created first building
- [ ] Imported or created building data
- [ ] Explored AI agent features
- [ ] Exported building data
- [ ] Shared project with team

### **Basic Proficiency**
- [ ] Understand SVGX format basics
- [ ] Can use CLI for common tasks
- [ ] Know how to interact with AI agent
- [ ] Can export data in multiple formats
- [ ] Understand building system concepts
- [ ] Can create and manage work orders

### **Ready for Advanced Features**
- [ ] Familiar with all basic features
- [ ] Understand integration concepts
- [ ] Know how to get help and support
- [ ] Ready to explore advanced capabilities
- [ ] Prepared for team collaboration

---

## 🚀 **What's Next?**

### **Immediate Next Steps**
1. **Complete Tutorials**: Work through the basic tutorials
2. **Explore Features**: Try different features and capabilities
3. **Join Community**: Connect with other Arxos users
4. **Set Up Team**: Invite team members to collaborate

### **Advanced Learning**
1. **API Integration**: Learn to use Arxos APIs
2. **Automation**: Set up automated workflows
3. **Enterprise Features**: Explore enterprise capabilities
4. **Custom Development**: Build custom integrations

### **Professional Development**
1. **Certification**: Consider Arxos certification
2. **Training**: Attend Arxos training sessions
3. **Conferences**: Join Arxos user conferences
4. **Contributing**: Contribute to the Arxos community

---

**Congratulations!** You've successfully started your journey with Arxos. The platform is designed to grow with your needs, from simple building visualization to complex enterprise management. Take your time exploring features and don't hesitate to ask for help when needed.

**Need Help?** Contact our support team or use the AI assistant for immediate assistance. 
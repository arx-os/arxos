# 🚀 Quick Start: MCP-Engineering Production Deployment

## 🎯 What You're Deploying

You're about to deploy a **production-ready engineering validation system** that includes:

- ✅ **Real-time Building Code Validation** (IBC, NEC, ASHRAE, IPC, IFC, ADA, NFPA)
- ✅ **AI-Powered Compliance Checking** with ML models
- ✅ **Cross-System Analysis** and impact assessment
- ✅ **Professional PDF Reports** with email delivery
- ✅ **WebSocket Real-time Updates** for CAD integration
- ✅ **Enterprise Monitoring** (Prometheus + Grafana)
- ✅ **Advanced Caching** with Redis
- ✅ **Knowledge Base System** with jurisdiction management
- ✅ **Production-Ready API** with authentication and RBAC

## ⚡ Quick Deployment (5 Minutes)

### Option 1: One-Command Deployment
```bash
cd services/mcp
./deploy-production.sh
```

### Option 2: Manual Deployment
```bash
cd services/mcp

# 1. Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# 2. Check status
docker-compose -f docker-compose.prod.yml ps

# 3. Test the service
curl http://localhost:8001/health
```

## 🌐 Access Your Services

Once deployed, you can access:

| Service | URL | Purpose |
|---------|-----|---------|
| **MCP Service** | http://localhost:8001 | Main API |
| **API Docs** | http://localhost:8001/docs | Swagger UI |
| **Health Check** | http://localhost:8001/health | Service status |
| **Grafana** | http://localhost:3000 | Monitoring dashboards |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **MLflow** | http://localhost:5000 | ML model management |

## 🧪 Test Your Deployment

### 1. Health Check
```bash
curl http://localhost:8001/health
```

### 2. Authentication Test
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. Building Validation Test
```bash
# Get token from previous step
TOKEN="your_token_here"

curl -X POST http://localhost:8001/api/v1/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "building_data": {
      "area": 8000,
      "height": 25,
      "type": "commercial",
      "occupancy": "B"
    },
    "validation_type": "structural"
  }'
```

### 4. Knowledge Base Test
```bash
curl -X POST http://localhost:8001/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "occupant load calculation",
    "code_standard": "IBC",
    "max_results": 5
  }'
```

### 5. ML Integration Test
```bash
curl -X POST http://localhost:8001/api/v1/ml/validate \
  -H "Content-Type: application/json" \
  -d '{
    "building_data": {
      "area": 12000,
      "height": 30,
      "type": "commercial"
    },
    "validation_type": "structural",
    "include_suggestions": true
  }'
```

## 📊 Monitor Your System

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f mcp-service
```

### Check Performance
```bash
# Service metrics
curl http://localhost:8001/metrics

# Cache statistics
curl http://localhost:8001/api/v1/cache/stats
```

### Grafana Dashboards
1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. View pre-configured dashboards:
   - **Performance Dashboard**: Real-time system metrics
   - **Business Intelligence**: User activity and trends
   - **Compliance Analytics**: Validation statistics
   - **System Health**: Infrastructure monitoring

## 🔧 Management Commands

### Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Update Services
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### View Resource Usage
```bash
docker stats
```

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs mcp-service

# Check if ports are available
netstat -tulpn | grep :8001
```

### Database Issues
```bash
# Check database connection
docker-compose -f docker-compose.prod.yml exec postgres-prod pg_isready

# Reset database
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Check cache performance
curl http://localhost:8001/api/v1/cache/stats
```

## 🔒 Security Configuration

### 1. Change Default Passwords
```bash
# Edit .env.production
nano .env.production

# Update these values:
JWT_SECRET_KEY=your-secure-jwt-secret
PROD_DB_PASSWORD=your-secure-db-password
GRAFANA_PASSWORD=your-secure-grafana-password
```

### 2. Configure SSL
```bash
# Add SSL certificates to nginx/ssl/
# Update nginx configuration
```

### 3. Set Up Firewall
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8001/tcp
```

## 📈 Production Scaling

### Horizontal Scaling
```bash
# Scale MCP service
docker-compose -f docker-compose.prod.yml up -d --scale mcp-service=3
```

### Load Balancer
```bash
# Configure nginx load balancer
# Update nginx/nginx.conf
```

### Database Scaling
```bash
# Add read replicas
# Configure connection pooling
```

## 🎯 Next Steps

### Immediate (This Week)
1. ✅ Deploy to staging environment
2. ✅ Run integration tests
3. ✅ Configure monitoring alerts
4. ✅ Set up SSL certificates
5. ✅ Configure email settings

### Short Term (Next Week)
1. 🔄 Deploy to production
2. 🔄 Set up CI/CD pipeline
3. 🔄 Configure backup strategy
4. 🔄 Set up logging aggregation
5. 🔄 Configure auto-scaling

### Medium Term (Next Month)
1. 🔄 Advanced ML model training
2. 🔄 Predictive analytics features
3. 🔄 Mobile app integration
4. 🔄 Advanced reporting features
5. 🔄 Multi-tenant architecture

## 📞 Support

- **Documentation**: [DEPLOYMENT_PRODUCTION.md](DEPLOYMENT_PRODUCTION.md)
- **API Reference**: http://localhost:8001/docs
- **Monitoring**: http://localhost:3000
- **Logs**: `docker-compose -f docker-compose.prod.yml logs`

---

**🎉 Congratulations!** You now have a production-ready engineering validation system that can:

- Validate building designs against all major codes
- Provide AI-powered compliance recommendations
- Generate professional reports
- Monitor system performance in real-time
- Scale to handle enterprise workloads

**Status**: ✅ Ready for Production Use 
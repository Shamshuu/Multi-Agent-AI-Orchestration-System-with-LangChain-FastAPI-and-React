FROM node:20-alpine

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install node dependencies
RUN npm install

# Copy application source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

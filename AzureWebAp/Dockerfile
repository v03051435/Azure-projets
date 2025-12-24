# ========= Build stage =========
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# 拷贝 csproj 并 restore（加速）
COPY *.csproj ./
RUN dotnet restore

# 拷贝其余代码并发布
COPY . .
RUN dotnet publish -c Release -o /app/publish

# ========= Runtime stage =========
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app

COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080

ENTRYPOINT ["dotnet", "AzureWebAp.dll"]

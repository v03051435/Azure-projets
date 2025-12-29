using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;

namespace AzureWebApi2.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class Data2Controller : ControllerBase
    {
        private readonly IWebHostEnvironment _env;
        private readonly IConfiguration _config;

        public Data2Controller(IWebHostEnvironment env, IConfiguration config)
        {
            _env = env;
            _config = config;
        }

        [HttpGet]
        public IActionResult GetData()
        {
            var envName = _env.EnvironmentName;
            var data = new List<DataObject>();
            for (int i = 1; i <= 4; i++)
            {
                data.Add(new DataObject
                {
                    Id = i,
                    Name = $"Env : {envName}, Item {i}",
                    Description = $"Api 2 : {i}."
                });
            }
            return Ok(data);
        }

        // GET /data/env -> returns current environment and a sample app setting
        [HttpGet("env")]
        public IActionResult GetEnvironment()
        {
            var envName = _env.EnvironmentName;
            // example of reading a value that can be overridden in appsettings.{ENV}.json
            var sample = _config["App:Name"] ?? _config["EnvironmentDisplay"];
            return Ok(new { environment = envName, sampleSetting = sample });
        }

        public class DataObject
        {
            public int Id { get; set; }
            public required string Name { get; set; }
            public string Description { get; set; }
        }
    }
}

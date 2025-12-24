using Microsoft.AspNetCore.Mvc;

namespace AzureWebAp.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class DataController : ControllerBase
    {
        [HttpGet]
        public IActionResult GetData()
        {
            var data = new List<DataObject>();
            for (int i = 1; i <= 10; i++)
            {
                data.Add(new DataObject
                {
                    Id = i,
                    Name = $"Item {i}",
                    Description = $"This is the description for item {i}."
                });
            }
            return Ok(data);
        }

        public class DataObject
        {
            public int Id { get; set; }
            public required string Name { get; set; }
            public string Description { get; set; }
        }
    }
}

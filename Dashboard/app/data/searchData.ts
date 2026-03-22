export interface KeywordAggregateData {
  query: string;
  impressions: number;
  clicks: number;
  ctr: number;
  averagePosition: number;
}

export interface QueryData {
  query: string;
  impressions: number;
  clicks: number;
  ctr: number;
  averagePosition: number;
}

export interface DetailedDateData {
  date: string;
  queries: QueryData[];
}

export const DetailedSearchQueryData: DetailedDateData[] = [
  {
    date: "2023-01-01",
    queries: [
      {
        query: "example query 1",
        impressions: 1500,
        clicks: 100,
        ctr: 6.67,
        averagePosition: 20.1,
      },
      {
        query: "another search term",
        impressions: 2000,
        clicks: 150,
        ctr: 7.5,
        averagePosition: 25.3,
      },
      {
        query: "product type A",
        impressions: 800,
        clicks: 60,
        ctr: 7.5,
        averagePosition: 30.5,
      },
      {
        query: "brand name xyz",
        impressions: 1000,
        clicks: 78,
        ctr: 7.8,
        averagePosition: 18.9,
      },
    ],
  },
  {
    date: "2023-01-08",
    queries: [
      {
        query: "example query 1",
        impressions: 1700,
        clicks: 120,
        ctr: 7.06,
        averagePosition: 18.5,
      },
      {
        query: "another search term",
        impressions: 2200,
        clicks: 170,
        ctr: 7.73,
        averagePosition: 23.0,
      },
      {
        query: "product type A",
        impressions: 900,
        clicks: 70,
        ctr: 7.78,
        averagePosition: 28.1,
      },
      {
        query: "brand name xyz",
        impressions: 1100,
        clicks: 85,
        ctr: 7.73,
        averagePosition: 17.5,
      },
      {
        query: "service offering B",
        impressions: 350,
        clicks: 27,
        ctr: 7.71,
        averagePosition: 33.2,
      },
    ],
  },
  {
    date: "2023-01-15",
    queries: [
      {
        query: "example query 1",
        impressions: 1850,
        clicks: 135,
        ctr: 7.3,
        averagePosition: 17.2,
      },
      {
        query: "another search term",
        impressions: 2400,
        clicks: 185,
        ctr: 7.71,
        averagePosition: 21.5,
      },
      {
        query: "product type A",
        impressions: 1000,
        clicks: 80,
        ctr: 8.0,
        averagePosition: 26.8,
      },
      {
        query: "brand name xyz",
        impressions: 1200,
        clicks: 90,
        ctr: 7.5,
        averagePosition: 16.0,
      },
      {
        query: "service offering B",
        impressions: 400,
        clicks: 30,
        ctr: 7.5,
        averagePosition: 31.5,
      },
      {
        query: "how to do something",
        impressions: 200,
        clicks: 15,
        ctr: 7.5,
        averagePosition: 40.0,
      },
    ],
  },
  {
    date: "2023-01-22",
    queries: [
      {
        query: "example query 1",
        impressions: 2000,
        clicks: 150,
        ctr: 7.5,
        averagePosition: 16.0,
      },
      {
        query: "another search term",
        impressions: 2600,
        clicks: 200,
        ctr: 7.69,
        averagePosition: 20.0,
      },
      {
        query: "product type A",
        impressions: 1100,
        clicks: 85,
        ctr: 7.73,
        averagePosition: 25.5,
      },
      {
        query: "brand name xyz",
        impressions: 1300,
        clicks: 100,
        ctr: 7.69,
        averagePosition: 15.0,
      },
      {
        query: "service offering B",
        impressions: 450,
        clicks: 35,
        ctr: 7.78,
        averagePosition: 30.0,
      },
      {
        query: "how to do something",
        impressions: 250,
        clicks: 20,
        ctr: 8.0,
        averagePosition: 38.0,
      },
      {
        query: "long tail product query",
        impressions: 120,
        clicks: 8,
        ctr: 6.67,
        averagePosition: 45.0,
      },
    ],
  },
  {
    date: "2023-01-29",
    queries: [
      {
        query: "example query 1",
        impressions: 2100,
        clicks: 155,
        ctr: 7.38,
        averagePosition: 15.5,
      },
      {
        query: "another search term",
        impressions: 2700,
        clicks: 205,
        ctr: 7.59,
        averagePosition: 19.5,
      },
      {
        query: "product type A",
        impressions: 1150,
        clicks: 88,
        ctr: 7.65,
        averagePosition: 25.0,
      },
      {
        query: "brand name xyz",
        impressions: 1350,
        clicks: 102,
        ctr: 7.56,
        averagePosition: 14.8,
      },
      {
        query: "service offering B",
        impressions: 480,
        clicks: 36,
        ctr: 7.5,
        averagePosition: 29.5,
      },
      {
        query: "how to do something",
        impressions: 270,
        clicks: 20,
        ctr: 7.41,
        averagePosition: 37.5,
      },
      {
        query: "long tail product query",
        impressions: 150,
        clicks: 9,
        ctr: 6.0,
        averagePosition: 44.0,
      },
    ],
  },
];
